from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from agents import run_investigation
from mcp_clients.router import MCPClientError, MCPValidationError, call_mcp_tool


ROOT = Path(__file__).parent
WEB = ROOT / "web"


def _mcp_field_label(name: str) -> str:
    labels = {
        "drug": "Препарат",
        "gene": "Ген",
        "query": "Поисковый запрос",
        "drug_name": "Название препарата",
    }
    return labels.get(name, name.replace("_", " "))


def _validate_mcp_arguments(source: str, tool: str, arguments: dict[str, object]) -> None:
    from mcp_clients.router import list_mcp_catalog

    catalog = list_mcp_catalog()
    tools = catalog["external_tools"] if source == "external" else catalog["local_tools"]
    selected = next((item for item in tools if item["name"] == tool), None)
    if selected is None:
        raise ValueError("Инструмент MCP не найден")
    schema = selected.get("inputSchema", {})
    properties = schema.get("properties", {})
    missing = [name for name in schema.get("required", []) if arguments.get(name) is None or str(arguments.get(name, "")).strip() == ""]
    if missing:
        raise ValueError(f"Заполните: {', '.join(_mcp_field_label(name) for name in missing)}")
    for name, value in arguments.items():
        field = properties.get(name, {})
        field_type = field.get("type")
        if field_type in {"integer", "number"} and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise ValueError(f"Поле «{_mcp_field_label(name)}» должно быть числом")
        if field_type == "integer" and isinstance(value, float) and not value.is_integer():
            raise ValueError(f"Поле «{_mcp_field_label(name)}» должно быть целым числом")
        if field.get("minimum") is not None and value < field["minimum"]:
            raise ValueError(f"Поле «{_mcp_field_label(name)}» не может быть меньше {field['minimum']}")
        if field.get("maximum") is not None and value > field["maximum"]:
            raise ValueError(f"Поле «{_mcp_field_label(name)}» не может быть больше {field['maximum']}")


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
            self._send(b'{"status":"ok","mcp":true}', "application/json; charset=utf-8")
            return
        if path == "/api/mcp/catalog":
            try:
                from mcp_clients.router import list_mcp_catalog

                body = json.dumps(list_mcp_catalog(), ensure_ascii=False).encode()
                self._send(body, "application/json; charset=utf-8")
            except Exception as exc:
                self._send(json.dumps({"error": f"Не удалось загрузить каталог MCP: {exc}"}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 500)
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
        path = urlparse(self.path).path
        if path == "/api/mcp/call":
            self._handle_mcp_call()
            return
        if path != "/api/investigate":
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

    def _handle_mcp_call(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            source = str(payload.get("source", "")).strip()
            tool = str(payload.get("tool", "")).strip()
            arguments = payload.get("arguments") or {}
            if source not in {"stdio", "network", "external"}:
                raise ValueError("Выберите источник MCP")
            if not tool:
                raise ValueError("Выберите инструмент MCP")
            if not isinstance(arguments, dict):
                raise ValueError("Параметры инструмента должны быть объектом")
            _validate_mcp_arguments(source, tool, arguments)
            result = call_mcp_tool(source, tool, arguments)
            self._send(json.dumps(result, ensure_ascii=False).encode(), "application/json; charset=utf-8")
        except MCPValidationError as exc:
            self._send(json.dumps({"error": str(exc)}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 400)
        except MCPClientError as exc:
            self._send(json.dumps({"error": str(exc)}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 502)
        except ValueError as exc:
            self._send(json.dumps({"error": str(exc)}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 400)
        except Exception as exc:
            self._send(json.dumps({"error": f"Ошибка MCP: {exc}"}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 502)

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
