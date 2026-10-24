import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from lamassu.archive import Archive
from lamassu.demo import populate
from lamassu.server import make_server


class WorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temp.name) / "archive.sqlite"
        with Archive(cls.path) as archive:
            populate(archive)
        cls.before = cls.path.read_bytes()
        cls.token = "synthetic-test-access-key"
        cls.server = make_server(cls.path, 0, cls.token)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, path, method="GET", authorized=True, headers=None):
        connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=5
        )
        values = {"Authorization": "Bearer " + self.token} if authorized else {}
        values.update(headers or {})
        connection.request(method, path, headers=values)
        response = connection.getresponse()
        body = response.read()
        result = (response.status, dict(response.getheaders()), body)
        connection.close()
        return result

    def test_missing_or_wrong_key_cannot_read_data(self):
        self.assertEqual(self.request("/api/overview", authorized=False)[0], 401)
        self.assertEqual(
            self.request("/api/overview", headers={"Authorization": "Bearer wrong"})[0],
            401,
        )

    def test_overview_and_source_inspection_are_readonly(self):
        status, headers, raw = self.request("/api/overview")
        self.assertEqual(status, 200)
        data = json.loads(raw)
        self.assertEqual(data["stats"]["conversations"], 6)
        record_id = data["records"][0]["record_id"]
        detail = json.loads(self.request("/api/record?id=" + record_id)[2])
        self.assertEqual(len(detail["messages"]), 3)
        self.assertEqual(self.path.read_bytes(), self.before)

    def test_cross_origin_and_rebinding_are_refused(self):
        self.assertEqual(
            self.request(
                "/api/overview", headers={"Origin": "https://attacker.invalid"}
            )[0],
            403,
        )
        self.assertEqual(
            self.request("/api/overview", headers={"Host": "attacker.invalid"})[0], 403
        )

    def test_mutations_and_path_traversal_are_unavailable(self):
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            self.assertEqual(self.request("/api/record", method)[0], 405)
        for path in ["/../archive.sqlite", "/%2e%2e/archive.sqlite", "/api/absent"]:
            self.assertEqual(self.request(path)[0], 404)

    def test_static_assets_have_content_security_policy_and_no_remote_scripts(self):
        status, headers, raw = self.request("/", authorized=False)
        self.assertEqual(status, 200)
        self.assertIn("script-src 'self'", headers["Content-Security-Policy"])
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertNotIn(b"https://", raw)
        for path in ["/app.js", "/style.css", "/upbeam.jpg"]:
            self.assertEqual(self.request(path, authorized=False)[0], 200)

    def test_search_and_validation(self):
        status, _, raw = self.request("/api/search?q=offline")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(raw)["results"])
        self.assertEqual(self.request("/api/search?q=")[0], 400)
        self.assertEqual(self.request("/api/record?id=missing")[0], 400)
