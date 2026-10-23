"""Evidence-preserving local prototype; no network or agent execution."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone

MAX_BYTES = 8 * 1024 * 1024


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _text(value, limit=512, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError('expected text with content')
    if len(value) > limit or '\x00' in value:
        raise ValueError('text exceeds limits or contains NUL')
    try:
        value.encode('utf-8')
    except UnicodeEncodeError as exc:
        raise ValueError('invalid Unicode') from exc


def parse(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('input exceeds 8 MiB')
    try:
        record = json.loads(raw.decode('utf-8'), object_pairs_hook=_object)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError('expected bounded UTF-8 JSON') from exc
    if not isinstance(record, dict) or set(record) != {'schema', 'provider', 'external_id', 'messages'}:
        raise ValueError('invalid conversation fields')
    if record['schema'] != 'lamassu.conversation.v1':
        raise ValueError('unsupported schema')
    _text(record['provider'])
    _text(record['external_id'])
    messages = record['messages']
    if not isinstance(messages, list) or not 1 <= len(messages) <= 10000:
        raise ValueError('expected 1 to 10000 messages')
    seen = set()
    for m in messages:
        if not isinstance(m, dict) or not {'id', 'role', 'text'} <= set(m) or set(m) - {'id', 'role', 'text', 'at'}:
            raise ValueError('invalid message fields')
        _text(m['id'])
        _text(m['role'])
        _text(m['text'], 1024 * 1024, empty=True)
        if m['id'] in seen or m['role'] not in {'user', 'assistant', 'system', 'tool'}:
            raise ValueError('duplicate id or invalid role')
        seen.add(m['id'])
        if 'at' in m:
            _text(m['at'], 64)
            value = m['at']
            try:
                parsed = datetime.fromisoformat(value[:-1] + '+00:00' if value.endswith('Z') else value)
                if 'T' not in value or parsed.utcoffset() is None:
                    raise ValueError()
            except ValueError as exc:
                raise ValueError('timestamp requires ISO date-time with offset') from exc
    return record


class Archive:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        try:
            version = self.connection.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise ValueError('unsupported database version')
            if version == 0:
                if self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                    raise ValueError('refusing nonempty unversioned database')
                with self.connection:
                    self.connection.execute('CREATE TABLE records (record_id TEXT PRIMARY KEY, provider TEXT, external_id TEXT, digest TEXT, imported_at TEXT, raw BLOB)')
                    self.connection.execute('CREATE TABLE messages (record_id TEXT REFERENCES records(record_id), message_id TEXT, role TEXT, text TEXT, at TEXT, PRIMARY KEY(record_id, message_id))')
                    self.connection.execute('PRAGMA user_version=1')
            self.connection.execute('PRAGMA foreign_keys=ON')
        except Exception:
            self.connection.close()
            raise

    def close(self):
        self.connection.close()

    def ingest(self, raw):
        record = parse(raw)
        digest = hashlib.sha256(raw).hexdigest()
        identity = json.dumps([record['provider'], record['external_id'], digest])
        record_id = hashlib.sha256(identity.encode()).hexdigest()
        with self.connection:
            added = self.connection.execute('INSERT OR IGNORE INTO records VALUES (?, ?, ?, ?, ?, ?)', (record_id, record['provider'], record['external_id'], digest, datetime.now(timezone.utc).isoformat(), raw)).rowcount
            if added:
                self.connection.executemany('INSERT INTO messages VALUES (?, ?, ?, ?, ?)', [(record_id, m['id'], m['role'], m['text'], m.get('at')) for m in record['messages']])
        return dict(record_id=record_id, digest=digest, added=bool(added))

    def search(self, query, limit=20):
        _text(query, 1000)
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('limit must be 1 to 100')
        rows = self.connection.execute('SELECT r.record_id, r.provider, r.external_id, r.digest, m.message_id, m.role, m.text, m.at FROM messages m JOIN records r USING(record_id) WHERE instr(lower(m.text), lower(?)) > 0 ORDER BY r.imported_at DESC, r.record_id, m.message_id LIMIT ?', (query, limit)).fetchall()
        return [dict(zip(('record_id', 'provider', 'external_id', 'digest', 'message_id', 'role', 'text', 'at'), row)) for row in rows]
