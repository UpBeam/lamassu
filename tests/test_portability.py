import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from lamassu.archive import Archive
from lamassu.demo import populate
from test_archive import fixture


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.archive = Archive(self.root / "source.sqlite")

    def tearDown(self):
        self.archive.close()
        self.temp.cleanup()

    def test_export_restore_preserves_bytes_links_and_timestamps(self):
        populate(self.archive)
        raw = self.archive.export()
        with Archive(self.root / "restored.sqlite") as restored:
            result = restored.restore(raw)
            self.assertEqual(result["records_added"], 6)
            self.assertEqual(restored.stats(), self.archive.stats())
            self.assertEqual(restored.export(), raw)
            self.assertTrue(restored.verify()["ok"])
            self.assertEqual(restored.restore(raw)["records_added"], 0)
            self.assertEqual(restored.export(), raw)

    def test_tampered_bundle_is_rejected_before_writes(self):
        populate(self.archive)
        pristine = json.loads(self.archive.export())
        cases = []
        bad = json.loads(json.dumps(pristine))
        bad["records"][-1]["digest"] = "f" * 64
        cases.append(bad)
        bad = json.loads(json.dumps(pristine))
        bad["records"][0]["raw_base64"] = "@@@"
        cases.append(bad)
        bad = json.loads(json.dumps(pristine))
        bad["links"][0]["source_id"] = "f" * 64
        cases.append(bad)
        bad = json.loads(json.dumps(pristine))
        bad["records"].append(bad["records"][0])
        cases.append(bad)
        bad = json.loads(json.dumps(pristine))
        bad["links"][0]["relation"] = ["supports"]
        cases.append(bad)
        bad = json.loads(json.dumps(pristine))
        bad["records"][0]["imported_at"] = "yesterday"
        cases.append(bad)
        with Archive(self.root / "target.sqlite") as target:
            for case in cases:
                with (
                    self.subTest(case=case["records"][0]["record_id"]),
                    self.assertRaises(ValueError),
                ):
                    target.restore(json.dumps(case).encode())
                self.assertEqual(target.stats()["revisions"], 0)
                self.assertEqual(target.stats()["links"], 0)

    def test_failure_during_restore_rolls_back_all_records(self):
        populate(self.archive)
        with Archive(self.root / "target.sqlite") as target:
            target.connection.execute(
                "CREATE TRIGGER reject_message BEFORE INSERT ON messages WHEN (SELECT count(*) FROM records)>1 BEGIN SELECT RAISE(ABORT, 'synthetic interruption'); END"
            )
            with self.assertRaises(sqlite3.IntegrityError):
                target.restore(self.archive.export())
            self.assertEqual(target.stats()["revisions"], 0)
            self.assertEqual(target.stats()["messages"], 0)

    def test_verify_detects_altered_projection_and_export_refuses(self):
        self.archive.ingest(fixture())
        with self.archive.connection:
            self.archive.connection.execute("UPDATE messages SET text='altered'")
        self.assertFalse(self.archive.verify()["ok"])
        with self.assertRaises(ValueError):
            self.archive.export()

    def test_verify_detects_source_digest_and_metadata_changes(self):
        self.archive.ingest(fixture())
        for column, value in [
            ("digest", "f" * 64),
            ("provider", "other"),
            ("imported_at", "not a time"),
        ]:
            with self.subTest(column=column):
                self.archive.connection.execute("SAVEPOINT synthetic")
                self.archive.connection.execute(
                    f"UPDATE records SET {column}=?", (value,)
                )
                self.assertFalse(self.archive.verify()["ok"])
                self.archive.connection.execute("ROLLBACK TO synthetic")
                self.archive.connection.execute("RELEASE synthetic")

    def test_link_references_existing_revisions_and_is_idempotent(self):
        a = self.archive.ingest(fixture())["record_id"]
        b = self.archive.ingest(fixture(external_id="second"))["record_id"]
        self.assertTrue(
            self.archive.link(a, b, "supports", "An explicitly authored reason")[
                "added"
            ]
        )
        self.assertFalse(
            self.archive.link(a, b, "supports", "An explicitly authored reason")[
                "added"
            ]
        )
        self.assertEqual(len(self.archive.get(a)["links"]), 1)
        for source, target, relation in [
            (a, a, "supports"),
            (a, "f" * 64, "supports"),
            (a, b, "invented"),
        ]:
            with self.assertRaises(ValueError):
                self.archive.link(source, target, relation, "reason")

    def test_unicode_search_and_original_message_order(self):
        record = json.loads(fixture())
        record["messages"] = [
            dict(id="z", role="user", text="Straße"),
            dict(id="a", role="assistant", text="ÅLAND"),
        ]
        result = self.archive.ingest(json.dumps(record).encode())
        self.assertEqual(self.archive.search("STRASSE")[0]["message_id"], "z")
        self.assertEqual(self.archive.search("åland")[0]["message_id"], "a")
        self.assertEqual(
            [
                m["message_id"]
                for m in self.archive.get(result["record_id"])["messages"]
            ],
            ["z", "a"],
        )

    def test_readonly_never_creates_or_modifies_archive(self):
        with self.assertRaises(sqlite3.OperationalError):
            Archive(self.root / "absent.sqlite", readonly=True)
        self.assertFalse((self.root / "absent.sqlite").exists())
        self.archive.ingest(fixture())
        before = (self.root / "source.sqlite").read_bytes()
        with Archive(self.root / "source.sqlite", readonly=True) as archive:
            self.assertEqual(len(archive.search("guardian")), 1)
            with self.assertRaises(sqlite3.OperationalError):
                archive.ingest(fixture(external_id="other"))
        self.assertEqual((self.root / "source.sqlite").read_bytes(), before)

    def test_migrate_v1_preserves_original_evidence(self):
        raw = fixture()
        path = self.root / "old.sqlite"
        digest = hashlib.sha256(raw).hexdigest()
        record_id = hashlib.sha256(
            json.dumps(["synthetic", "demo", digest]).encode()
        ).hexdigest()
        with sqlite3.connect(path) as db:
            db.execute(
                "CREATE TABLE records (record_id TEXT PRIMARY KEY, provider TEXT, external_id TEXT, digest TEXT, imported_at TEXT, raw BLOB)"
            )
            db.execute(
                "CREATE TABLE messages (record_id TEXT REFERENCES records(record_id), message_id TEXT, role TEXT, text TEXT, at TEXT, PRIMARY KEY(record_id,message_id))"
            )
            db.execute(
                "INSERT INTO records VALUES (?,?,?,?,?,?)",
                (
                    record_id,
                    "synthetic",
                    "demo",
                    digest,
                    "2026-10-24T12:00:00+00:00",
                    raw,
                ),
            )
            db.execute(
                "INSERT INTO messages VALUES (?,?,?,?,?)",
                (
                    record_id,
                    "m1",
                    "user",
                    "A guardian preserves evidence.",
                    "2026-10-24T12:00:00Z",
                ),
            )
            db.execute("PRAGMA user_version=1")
        with Archive(path) as migrated:
            self.assertEqual(migrated.stats()["schema_version"], 2)
            self.assertTrue(migrated.verify()["ok"])
            self.assertEqual(
                migrated.connection.execute("SELECT raw FROM records").fetchone()[0],
                raw,
            )
