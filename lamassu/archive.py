"""Local evidence archive. Imported content never executes or grants authority."""

import base64
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MAX_BYTES = 8 * 1024 * 1024
MAX_BUNDLE_BYTES = 64 * 1024 * 1024
SCHEMA_VERSION = 2
RELATIONS = {
    "continues",
    "supports",
    "contradicts",
    "supersedes",
    "implements",
    "derived-from",
}


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _text(value, limit=512, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError("expected text with content")
    if len(value) > limit or "\x00" in value:
        raise ValueError("text exceeds limits or contains NUL")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("invalid Unicode") from exc


def _timestamp(value):
    _text(value, 64)
    try:
        parsed = datetime.fromisoformat(
            value[:-1] + "+00:00" if value.endswith("Z") else value
        )
        if "T" not in value or parsed.utcoffset() is None:
            raise ValueError()
    except ValueError as exc:
        raise ValueError("timestamp requires ISO date-time with offset") from exc


def _json(raw, limit=MAX_BYTES):
    if len(raw) > limit:
        raise ValueError("input exceeds size limit")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_object)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError("expected bounded UTF-8 JSON") from exc


def parse(raw):
    record = _json(raw)
    if not isinstance(record, dict) or set(record) != {
        "schema",
        "provider",
        "external_id",
        "messages",
    }:
        raise ValueError("invalid conversation fields")
    if record["schema"] != "lamassu.conversation.v1":
        raise ValueError("unsupported conversation schema")
    _text(record["provider"])
    _text(record["external_id"])
    messages = record["messages"]
    if not isinstance(messages, list) or not 1 <= len(messages) <= 10000:
        raise ValueError("expected 1 to 10000 messages")
    seen = set()
    for m in messages:
        if (
            not isinstance(m, dict)
            or not {"id", "role", "text"} <= set(m)
            or set(m) - {"id", "role", "text", "at"}
        ):
            raise ValueError("invalid message fields")
        _text(m["id"])
        _text(m["role"])
        _text(m["text"], 1024 * 1024, empty=True)
        if m["id"] in seen or m["role"] not in {"user", "assistant", "system", "tool"}:
            raise ValueError("duplicate message id or invalid role")
        seen.add(m["id"])
        if "at" in m:
            _timestamp(m["at"])
    return record


def identity(record, raw):
    digest = hashlib.sha256(raw).hexdigest()
    key = json.dumps([record["provider"], record["external_id"], digest])
    return hashlib.sha256(key.encode()).hexdigest(), digest


def _limit(value, maximum=100):
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"limit must be 1 to {maximum}")


class Archive:
    def __init__(self, path, readonly=False):
        self.path = Path(path)
        self.readonly = readonly
        if self.path.is_symlink():
            raise ValueError("archive path must not be a symlink")
        if not readonly:
            try:
                fd = os.open(
                    self.path,
                    os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                )
            except FileExistsError:
                if self.path.is_symlink():
                    raise ValueError("archive path must not be a symlink")
            else:
                os.close(fd)
        if readonly:
            self.connection = sqlite3.connect(
                self.path.resolve().as_uri() + "?mode=ro", uri=True
            )
        else:
            self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        try:
            self.connection.create_function(
                "casefold",
                1,
                lambda value: value.casefold() if value is not None else "",
            )
            self.connection.execute("PRAGMA foreign_keys=ON")
            if readonly:
                self.connection.execute("PRAGMA query_only=ON")
            version = self.connection.execute("PRAGMA user_version").fetchone()[0]
            if readonly and version != SCHEMA_VERSION:
                raise ValueError(
                    "open archive in write mode once to initialize or migrate it"
                )
            if not readonly:
                self.connection.execute("BEGIN IMMEDIATE")
                # Re-read under the write lock; another process may have migrated it.
                version = self.connection.execute("PRAGMA user_version").fetchone()[0]
                if version not in (0, 1, SCHEMA_VERSION):
                    raise ValueError("unsupported database version")
                if version == 0:
                    if self.connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall():
                        raise ValueError("refusing nonempty unversioned database")
                    self.connection.execute(
                        "CREATE TABLE records (record_id TEXT PRIMARY KEY, provider TEXT NOT NULL, external_id TEXT NOT NULL, digest TEXT NOT NULL, imported_at TEXT NOT NULL, raw BLOB NOT NULL)"
                    )
                    self.connection.execute(
                        "CREATE TABLE messages (record_id TEXT NOT NULL REFERENCES records(record_id), message_id TEXT NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL, at TEXT, PRIMARY KEY(record_id, message_id))"
                    )
                if version < 2:
                    self.connection.execute(
                        "CREATE TABLE links (link_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES records(record_id), target_id TEXT NOT NULL REFERENCES records(record_id), relation TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL)"
                    )
                    self.connection.execute(
                        "CREATE INDEX messages_record ON messages(record_id)"
                    )
                self.connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                self.connection.commit()
        except Exception:
            self.connection.rollback()
            self.connection.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        self.connection.close()

    def _ingest(self, raw, imported_at):
        record = parse(raw)
        record_id, digest = identity(record, raw)
        added = self.connection.execute(
            "INSERT OR IGNORE INTO records VALUES (?, ?, ?, ?, ?, ?)",
            (
                record_id,
                record["provider"],
                record["external_id"],
                digest,
                imported_at,
                raw,
            ),
        ).rowcount
        if added:
            self.connection.executemany(
                "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
                [
                    (record_id, m["id"], m["role"], m["text"], m.get("at"))
                    for m in record["messages"]
                ],
            )
        return dict(record_id=record_id, digest=digest, added=bool(added))

    def ingest(self, raw):
        parse(raw)
        with self.connection:
            return self._ingest(raw, datetime.now(timezone.utc).isoformat())

    def stats(self):
        result = dict(
            self.connection.execute(
                "SELECT count(*) AS revisions, count(DISTINCT provider || char(0) || external_id) AS conversations, coalesce(sum(length(raw)), 0) AS source_bytes FROM records"
            ).fetchone()
        )
        result["messages"] = self.connection.execute(
            "SELECT count(*) FROM messages"
        ).fetchone()[0]
        result["links"] = self.connection.execute(
            "SELECT count(*) FROM links"
        ).fetchone()[0]
        result["providers"] = [
            dict(row)
            for row in self.connection.execute(
                "SELECT provider, count(*) AS revisions FROM records GROUP BY provider ORDER BY provider"
            )
        ]
        result["schema_version"] = SCHEMA_VERSION
        return result

    def records(self, limit=100):
        _limit(limit)
        return [
            dict(row)
            for row in self.connection.execute(
                "SELECT r.record_id, r.provider, r.external_id, r.digest, r.imported_at, length(r.raw) AS source_bytes, count(m.message_id) AS messages FROM records r LEFT JOIN messages m USING(record_id) GROUP BY r.record_id ORDER BY r.imported_at DESC, r.record_id LIMIT ?",
                (limit,),
            )
        ]

    def get(self, record_id):
        row = self.connection.execute(
            "SELECT record_id, provider, external_id, digest, imported_at, length(raw) AS source_bytes, raw FROM records WHERE record_id=?",
            (record_id,),
        ).fetchone()
        if row is None:
            raise ValueError("record not found")
        record = dict(row)
        original = parse(record.pop("raw"))
        expected_id, digest = identity(original, row["raw"])
        if (expected_id, digest, original["provider"], original["external_id"]) != (
            record_id,
            record["digest"],
            record["provider"],
            record["external_id"],
        ):
            raise ValueError("source verification failed")
        _timestamp(record["imported_at"])
        expected = [
            (m["id"], m["role"], m["text"], m.get("at")) for m in original["messages"]
        ]
        projected = [
            tuple(m)
            for m in self.connection.execute(
                "SELECT message_id, role, text, at FROM messages WHERE record_id=? ORDER BY rowid",
                (record_id,),
            )
        ]
        if expected != projected:
            raise ValueError("source message projection failed verification")
        record["messages"] = [
            dict(message_id=m["id"], role=m["role"], text=m["text"], at=m.get("at"))
            for m in original["messages"]
        ]
        record["links"] = self.links(record_id)
        return record

    def search(self, query, limit=20):
        _text(query, 1000)
        _limit(limit)
        rows = self.connection.execute(
            "SELECT r.record_id, r.provider, r.external_id, r.digest, m.message_id, m.role, m.text, m.at FROM messages m JOIN records r USING(record_id) WHERE instr(casefold(m.text), casefold(?)) > 0 ORDER BY r.imported_at DESC, r.record_id, m.rowid LIMIT ?",
            (query, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def links(self, record_id=None):
        if record_id:
            rows = self.connection.execute(
                "SELECT * FROM links WHERE source_id=? OR target_id=? ORDER BY created_at, link_id",
                (record_id, record_id),
            )
        else:
            rows = self.connection.execute(
                "SELECT * FROM links ORDER BY created_at, link_id"
            )
        return [dict(row) for row in rows]

    def link(self, source_id, target_id, relation, reason):
        if relation not in RELATIONS or source_id == target_id:
            raise ValueError("invalid relation or self-link")
        _text(reason, 4000)
        self.get(source_id)
        self.get(target_id)
        key = json.dumps([source_id, target_id, relation, reason])
        link_id = hashlib.sha256(key.encode()).hexdigest()
        with self.connection:
            added = self.connection.execute(
                "INSERT OR IGNORE INTO links VALUES (?, ?, ?, ?, ?, ?)",
                (
                    link_id,
                    source_id,
                    target_id,
                    relation,
                    reason,
                    datetime.now(timezone.utc).isoformat(),
                ),
            ).rowcount
        return dict(link_id=link_id, added=bool(added))

    def verify(self):
        """Compare stored bytes, identities, and projected messages. Not authentication."""
        errors = []
        for row in self.connection.execute("SELECT * FROM records ORDER BY record_id"):
            try:
                record = parse(row["raw"])
                record_id, digest = identity(record, row["raw"])
                if (record_id, digest, record["provider"], record["external_id"]) != (
                    row["record_id"],
                    row["digest"],
                    row["provider"],
                    row["external_id"],
                ):
                    raise ValueError("record identity or metadata mismatch")
                _timestamp(row["imported_at"])
                expected = [
                    (m["id"], m["role"], m["text"], m.get("at"))
                    for m in record["messages"]
                ]
                actual = [
                    tuple(m)
                    for m in self.connection.execute(
                        "SELECT message_id, role, text, at FROM messages WHERE record_id=? ORDER BY rowid",
                        (record_id,),
                    )
                ]
                if expected != actual:
                    raise ValueError("message projection mismatch")
            except (ValueError, TypeError) as exc:
                errors.append(dict(record_id=row["record_id"], error=str(exc)))
        for row in self.connection.execute("PRAGMA foreign_key_check"):
            errors.append(
                dict(record_id=None, error=f"foreign key violation in {row[0]}")
            )
        for link in self.links():
            try:
                _text(link["reason"], 4000)
                _timestamp(link["created_at"])
                key = json.dumps(
                    [
                        link["source_id"],
                        link["target_id"],
                        link["relation"],
                        link["reason"],
                    ]
                )
                if (
                    link["relation"] not in RELATIONS
                    or link["source_id"] == link["target_id"]
                    or hashlib.sha256(key.encode()).hexdigest() != link["link_id"]
                ):
                    raise ValueError("link identity or relation mismatch")
            except (ValueError, TypeError) as exc:
                errors.append(dict(record_id=None, error=str(exc)))
        return dict(
            ok=not errors, errors=errors, records_checked=self.stats()["revisions"]
        )

    def export(self):
        check = self.verify()
        if not check["ok"]:
            raise ValueError("archive verification failed; refusing export")
        records = [
            dict(
                record_id=row["record_id"],
                digest=row["digest"],
                imported_at=row["imported_at"],
                raw_base64=base64.b64encode(row["raw"]).decode("ascii"),
            )
            for row in self.connection.execute(
                "SELECT * FROM records ORDER BY record_id"
            )
        ]
        bundle = dict(schema="lamassu.bundle.v1", records=records, links=self.links())
        raw = json.dumps(bundle, ensure_ascii=True, indent=2).encode("utf-8") + b"\n"
        if len(raw) > MAX_BUNDLE_BYTES:
            raise ValueError("bundle exceeds 64 MiB prototype limit")
        return raw

    def restore(self, raw):
        bundle = _json(raw, MAX_BUNDLE_BYTES)
        if (
            not isinstance(bundle, dict)
            or set(bundle) != {"schema", "records", "links"}
            or bundle["schema"] != "lamassu.bundle.v1"
        ):
            raise ValueError("unsupported bundle format")
        if (
            not isinstance(bundle["records"], list)
            or len(bundle["records"]) > 10000
            or not isinstance(bundle["links"], list)
            or len(bundle["links"]) > 10000
        ):
            raise ValueError("invalid bundle collections")
        prepared, seen = [], set()
        for item in bundle["records"]:
            if not isinstance(item, dict) or set(item) != {
                "record_id",
                "digest",
                "imported_at",
                "raw_base64",
            }:
                raise ValueError("invalid bundle record")
            try:
                source = base64.b64decode(item["raw_base64"], validate=True)
            except (ValueError, TypeError) as exc:
                raise ValueError("invalid encoded source") from exc
            record = parse(source)
            record_id, digest = identity(record, source)
            if (
                record_id != item["record_id"]
                or digest != item["digest"]
                or record_id in seen
            ):
                raise ValueError("bundle identity mismatch or duplicate record")
            _timestamp(item["imported_at"])
            seen.add(record_id)
            prepared.append((source, item["imported_at"]))
        # A bundle is self-contained: links may not rely on records already at destination.
        for item in bundle["links"]:
            if not isinstance(item, dict) or set(item) != {
                "link_id",
                "source_id",
                "target_id",
                "relation",
                "reason",
                "created_at",
            }:
                raise ValueError("invalid bundle link")
            if (
                not isinstance(item["relation"], str)
                or item["relation"] not in RELATIONS
                or item["source_id"] == item["target_id"]
            ):
                raise ValueError("invalid bundle relation")
            if (
                not isinstance(item["source_id"], str)
                or not isinstance(item["target_id"], str)
                or item["source_id"] not in seen
                or item["target_id"] not in seen
            ):
                raise ValueError("bundle link has missing evidence")
            _text(item["reason"], 4000)
            _timestamp(item["created_at"])
            key = json.dumps(
                [item["source_id"], item["target_id"], item["relation"], item["reason"]]
            )
            if item["link_id"] != hashlib.sha256(key.encode()).hexdigest():
                raise ValueError("bundle link identity mismatch")
        added = 0
        with self.connection:
            for source, imported_at in prepared:
                added += self._ingest(source, imported_at)["added"]
            for item in bundle["links"]:
                self.connection.execute(
                    "INSERT OR IGNORE INTO links VALUES (?, ?, ?, ?, ?, ?)",
                    tuple(
                        item[k]
                        for k in (
                            "link_id",
                            "source_id",
                            "target_id",
                            "relation",
                            "reason",
                            "created_at",
                        )
                    ),
                )
        return dict(
            records_added=added,
            records_seen=len(prepared),
            links_seen=len(bundle["links"]),
        )
