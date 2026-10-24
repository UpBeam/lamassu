import json
import tempfile
import unittest
from pathlib import Path
from lamassu.repository import inspect_repository


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_inventory_counts_components_without_running_scripts(self):
        package = self.root / "apps" / "example"
        package.mkdir(parents=True)
        (package / "package.json").write_text(
            json.dumps(
                dict(
                    name="synthetic-app",
                    dependencies={"a": "https://private.invalid/secret"},
                    scripts={"postinstall": "never execute this"},
                )
            )
        )
        (package / "index.ts").write_text(
            "This source body must not be parsed or executed."
        )
        report = inspect_repository(self.root)
        self.assertEqual(report["languages"], {"TypeScript": 1})
        self.assertEqual(report["packages"][0]["dependencies"], 1)
        self.assertNotIn("private.invalid", json.dumps(report))
        self.assertNotIn("postinstall", json.dumps(report))
        self.assertEqual(report["areas"], {"apps": 2})
        self.assertFalse(report["truncated"])

    def test_ignores_hidden_generated_and_symlinked_paths(self):
        for name in [".git", "node_modules", "dist"]:
            path = self.root / name
            path.mkdir()
            (path / "never.py").write_text("skip")
        (self.root / ".env").write_text("synthetic private material")
        (self.root / "private.key").write_text("skip")
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "external.py").write_text("skip")
        (self.root / "linked").symlink_to(outside, target_is_directory=True)
        (self.root / "file-link.py").symlink_to(outside / "external.py")
        (self.root / "allowed.py").write_text("pass")
        report = inspect_repository(self.root)
        self.assertEqual(report["files_counted"], 1)
        self.assertEqual(report["languages"], {"Python": 1})

    def test_reports_incomplete_coverage_and_malformed_manifest(self):
        (self.root / "package.json").write_text("{bad")
        report = inspect_repository(self.root)
        self.assertTrue(report["errors"])
        (self.root / "z.py").write_text("pass")
        report = inspect_repository(self.root, max_files=1)
        self.assertTrue(report["truncated"])
        self.assertEqual(report["files_counted"], 1)

    def test_commit_hint_is_metadata_not_execution(self):
        git = self.root / ".git"
        (git / "refs" / "heads").mkdir(parents=True)
        (git / "HEAD").write_text("ref: refs/heads/main")
        (git / "refs" / "heads" / "main").write_text("a" * 40)
        self.assertEqual(inspect_repository(self.root)["commit_hint"], "a" * 40)
        (git / "HEAD").write_text("ref: ../../outside")
        self.assertIsNone(inspect_repository(self.root)["commit_hint"])

    def test_symlink_root_is_rejected(self):
        link = Path(self.temp.name) / "alias"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            inspect_repository(link)
