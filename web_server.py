from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from agents import run_investigation


ROOT = Path(__file__).parent
WEB = ROOT / "web"


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send(b'{"status":"ok"}', "application/json; charset=utf-8")
            return
        if path == "/api/investigate":
            self._send('{"error":"Используйте POST"}'.encode(), "application/json; charset=utf-8", 405)
            return
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        requested = (WEB / relative).resolve()
        if WEB.resolve() not in requested.parents and requested != WEB.resolve():
            self._send(b"Not found", "text/plain; charset=utf-8", 404)
            return
        if not requested.is_file():
            self._send(b"Not found", "text/plain; charset=utf-8", 404)
            return
        content_types = {".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".json": "application/json"}
        self._send(requested.read_bytes(), f"{content_types.get(requested.suffix, 'application/octet-stream')}; charset=utf-8")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/investigate":
            self._send(b"Not found", "text/plain; charset=utf-8", 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            drug = str(payload.get("drug", "")).strip()
            gene = str(payload.get("gene", "")).strip()
            variant = str(payload.get("variant", "")).strip()
            if not drug or not gene:
                raise ValueError("Укажите препарат и ген")
            report = run_investigation(drug, gene, variant=variant)
            self._send(json.dumps(report.to_dict(), ensure_ascii=False).encode(), "application/json; charset=utf-8")
        except ValueError as exc:
            self._send(json.dumps({"error": str(exc)}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 400)
        except Exception as exc:
            self._send(json.dumps({"error": f"Не удалось собрать данные: {exc}"}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 500)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[web] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    host = os.environ.get("PHARMACOGEN_HOST", "127.0.0.1")
    port = int(os.environ.get("PHARMACOGEN_PORT", "8503"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"PharmacoGen web app: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
