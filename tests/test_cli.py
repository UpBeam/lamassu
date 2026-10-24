import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CommandTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-s", "-m", "lamassu", *map(str, args)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_demo_export_restore_and_verification_flow(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.sqlite"
            bundle = root / "bundle.json"
            restored = root / "restored.sqlite"
            result = self.run_cli("--database", source, "demo")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["messages"], 18)
            self.assertEqual(
                self.run_cli("--database", source, "export", bundle).returncode, 0
            )
            self.assertEqual(
                self.run_cli("--database", restored, "restore", bundle).returncode, 0
            )
            verified = self.run_cli("--database", restored, "verify")
            self.assertEqual(verified.returncode, 0, verified.stderr)
            self.assertTrue(json.loads(verified.stdout)["ok"])
            self.assertEqual(
                self.run_cli("--database", source, "export", bundle).returncode, 2
            )
            self.assertEqual(self.run_cli("--database", source, "demo").returncode, 2)

    def test_invalid_import_never_initializes_database(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "bad.json"
            source.write_text("{bad")
            db = root / "archive.sqlite"
            result = self.run_cli("--database", db, "import", source)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(db.exists())

    def test_missing_readonly_archive_is_not_created(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "missing.sqlite"
            result = self.run_cli("--database", db, "search", "anything")
            self.assertEqual(result.returncode, 2)
            self.assertFalse(db.exists())

    def test_passive_inventory_does_not_require_a_database(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            (repo / "sample.py").write_text("pass")
            output = root / "report.json"
            result = self.run_cli("inspect-repo", repo, "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text())["languages"], {"Python": 1})
