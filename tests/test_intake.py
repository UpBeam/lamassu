import json
import tempfile
import unittest
from pathlib import Path

from lamassu.intake import preview
import test_cli


class IntakeTests(unittest.TestCase):
    def test_neutral_is_ready_without_echoing_text(self):
        raw = json.dumps(
            dict(
                schema="lamassu.conversation.v1",
                provider="test",
                external_id="one",
                messages=[dict(id="1", role="user", text="PRIVATE SENTINEL")],
            )
        ).encode()
        result = preview(raw)
        self.assertTrue(result["import_ready"])
        self.assertEqual(result["message_entries"], 1)
        self.assertNotIn("PRIVATE SENTINEL", json.dumps(result))

    def test_mapping_counts_all_branches_without_claiming_import_support(self):
        raw = json.dumps(
            [
                dict(
                    mapping={
                        "root": {"message": None},
                        "a": {"message": {}},
                        "b": {"message": {}},
                    }
                )
            ]
        ).encode()
        result = preview(raw)
        self.assertEqual(result["message_entries"], 2)
        self.assertFalse(result["import_ready"])
        self.assertTrue(result["warnings"])

    def test_claude_structure_is_only_a_hint(self):
        result = preview(b'[{"chat_messages":[null]}]')
        self.assertEqual(result["format"], "claude-shaped-json")
        self.assertFalse(result["import_ready"])

    def test_duplicate_keys_and_invalid_neutral_rejected(self):
        for raw in (b'{"a":1,"a":2}', b'{"schema":"lamassu.conversation.v1"}'):
            with self.assertRaises(ValueError):
                preview(raw)

    def test_unknown_and_empty_export_not_claimed_as_supported(self):
        for raw in (b"[]", b"{}", b"null"):
            self.assertFalse(preview(raw)["import_ready"])

    def test_cli_does_not_initialize_database(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.json"
            source.write_text("[]")
            database = root / "must-not-exist.sqlite"
            result = test_cli.CommandTests.run_cli(
                self, "--database", database, "preview", source
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(database.exists())
