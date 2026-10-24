"""Loopback-only read-only workbench; not a production remote server."""

import hmac
import json
import secrets
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from .archive import Archive

WEB = Path(__file__).parent / "web"
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/upbeam.jpg": ("upbeam.jpg", "image/jpeg"),
}


def make_server(database, port=8765, token=None):
    database = Path(database).resolve()
    with Archive(database, readonly=True) as archive:
        archive.stats()
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("port must be 0 to 65535")
    token = token or secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        server_version = "Lamassu"
        sys_version = ""

        def log_message(self, *_):
            pass  # Do not log searches, source IDs, or credentials.

        def send_body(
            self, status, raw, content_type="application/json; charset=utf-8"
        ):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
            )
            self.end_headers()
            self.wfile.write(raw)

        def reply(self, status, value):
            self.send_body(status, json.dumps(value, ensure_ascii=True).encode())

        def do_POST(self):
            self.reply(405, {"error": "This workbench is read-only."})

        do_PUT = do_POST
        do_PATCH = do_POST
        do_DELETE = do_POST

        def do_GET(self):
            origin = f"http://127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                self.reply(403, {"error": "Host not permitted."})
                return
            if self.headers.get("Origin") not in (None, origin):
                self.reply(403, {"error": "Origin not permitted."})
                return
            if len(self.path) > 8192:
                self.reply(414, {"error": "Request too long."})
                return
            url = urlsplit(self.path)
            if url.path in STATIC:
                name, mime = STATIC[url.path]
                self.send_body(200, (WEB / name).read_bytes(), mime)
                return
            if not url.path.startswith("/api/"):
                self.reply(404, {"error": "Not found."})
                return
            supplied = self.headers.get("Authorization", "")
            if not hmac.compare_digest(supplied.encode(), ("Bearer " + token).encode()):
                self.reply(
                    401, {"error": "Open the access link printed by the local server."}
                )
                return
            try:
                query = parse_qs(url.query, keep_blank_values=True, max_num_fields=8)
                with Archive(database, readonly=True) as archive:
                    if url.path == "/api/overview":
                        links = archive.links()
                        result = dict(
                            stats=archive.stats(),
                            records=archive.records(),
                            links=links[:250],
                            links_truncated=len(links) > 250,
                        )
                    elif url.path == "/api/record":
                        result = archive.get(query.get("id", [""])[0])
                    elif url.path == "/api/search":
                        results = archive.search(query.get("q", [""])[0], limit=50)
                        for hit in results:
                            text = hit["text"]
                            hit["text"] = text[:1200]
                            hit["truncated"] = len(text) > 1200
                        result = dict(results=results, limit=50)
                    else:
                        self.reply(404, {"error": "Not found."})
                        return
                self.reply(200, result)
            except ValueError as exc:
                self.reply(400, {"error": str(exc)})
            except sqlite3.Error:
                self.reply(
                    500,
                    {"error": "Archive could not be read. Check the local archive."},
                )

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.access_url = f"http://127.0.0.1:{server.server_port}/#token={token}"
    return server


def serve(database, port=8765):
    server = make_server(database, port)
    print("Lamassu workbench · loopback only · read-only", flush=True)
    print(server.access_url, flush=True)
    print("Keep the access link private. Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
