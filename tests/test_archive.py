import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from lamassu.archive import Archive, MAX_BYTES, parse


def fixture(**changes):
    record = dict(
        schema="lamassu.conversation.v1",
        provider="synthetic",
        external_id="demo",
        messages=[
            dict(
                id="m1",
                role="user",
                text="A guardian preserves evidence.",
                at="2026-10-24T12:00:00Z",
            )
        ],
    )
    record.update(changes)
    return json.dumps(record).encode()


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "archive.sqlite"
        self.archive = Archive(self.path)

    def tearDown(self):
        self.archive.close()
        self.temp.cleanup()

    def test_idempotence_and_exact_bytes(self):
        raw = fixture()
        first = self.archive.ingest(raw)
        second = self.archive.ingest(raw)
        self.assertTrue(first["added"])
        self.assertFalse(second["added"])
        self.assertEqual(first["record_id"], second["record_id"])
        self.assertEqual(
            self.archive.connection.execute("SELECT raw FROM records").fetchone()[0],
            raw,
        )
        self.assertEqual(len(self.archive.search("GUARDIAN")), 1)

    def test_changed_export_keeps_both_revisions(self):
        first = self.archive.ingest(fixture())
        second = self.archive.ingest(
            fixture(
                messages=[
                    dict(id="m1", role="user", text="A guardian revises understanding.")
                ]
            )
        )
        self.assertNotEqual(first["record_id"], second["record_id"])
        self.assertEqual(len(self.archive.search("guardian")), 2)

    def test_provider_identity_is_separate(self):
        a = self.archive.ingest(fixture())
        b = self.archive.ingest(fixture(provider="other"))
        self.assertNotEqual(a["record_id"], b["record_id"])

    def test_invalid_records_leave_no_data(self):
        messages = [
            dict(id="a", role="user", text="x"),
            dict(id="a", role="tool", text="y"),
        ]
        cases = [
            fixture(messages=[]),
            fixture(provider=3),
            fixture(messages=messages),
            fixture(extra="bad"),
            fixture(messages=[dict(id="a", role="unknown", text="x")]),
            fixture(
                messages=[dict(id="a", role="user", text="x", at="2026-10-24T12:00:00")]
            ),
        ]
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.archive.ingest(raw)
        self.assertEqual(
            self.archive.connection.execute("SELECT count(*) FROM records").fetchone()[
                0
            ],
            0,
        )

    def test_bad_json_size_and_unicode(self):
        for raw in [
            b'{"schema":1,"schema":2}',
            b"\xff",
            b" " * (MAX_BYTES + 1),
            fixture(provider="\ud800"),
        ]:
            with self.subTest(raw=raw[:30]), self.assertRaises(ValueError):
                parse(raw)

    def test_literal_query_and_limits(self):
        self.archive.ingest(fixture())
        self.assertEqual(self.archive.search("' OR 1=1 --"), [])
        self.assertEqual(self.archive.search("%"), [])
        for query, limit in [
            ("", 20),
            ("guardian", 0),
            ("guardian", 101),
            ("guardian", True),
        ]:
            with self.assertRaises(ValueError):
                self.archive.search(query, limit)

    def test_reopen_preserves_provenance(self):
        self.archive.ingest(fixture())
        self.archive.close()
        self.archive = Archive(self.path)
        hit = self.archive.search("guardian")[0]
        self.assertEqual(hit["message_id"], "m1")
        self.assertEqual(hit["role"], "user")

    def test_unrelated_and_newer_databases_are_refused(self):
        for version in [0, 3]:
            path = Path(self.temp.name) / f"other{version}.sqlite"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE unrelated (value TEXT)")
                db.execute(f"PRAGMA user_version={version}")
            with self.assertRaises(ValueError):
                Archive(path)

    def test_failed_message_write_rolls_back_record(self):
        self.archive.connection.execute(
            "CREATE TRIGGER reject_message BEFORE INSERT ON messages BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.archive.ingest(fixture())
        self.assertEqual(
            self.archive.connection.execute("SELECT count(*) FROM records").fetchone()[
                0
            ],
            0,
        )
