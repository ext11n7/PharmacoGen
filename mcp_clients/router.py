"""Route web requests to the three MCP integration patterns.

The router deliberately keeps the transport boundary visible. Every call
returns a compact wire trace for the JSON-RPC inspector in the UI.
"""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import socket
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters


ROOT = Path(__file__).resolve().parents[1]
LOCAL_HTTP_URL = os.environ.get("PHARMACOGEN_LOCAL_MCP_URL", "http://127.0.0.1:8000/sse")
EXTERNAL_HTTP_URL = os.environ.get("PHARMACOGEN_EXTERNAL_MCP_URL", "").strip()
_network_process: subprocess.Popen[bytes] | None = None
_process_lock = threading.Lock()
_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_cache_lock = threading.Lock()
CACHE_TTL_SECONDS = 300


class MCPClientError(RuntimeError):
    """An expected, user-facing MCP transport or tool error."""


class MCPValidationError(MCPClientError):
    """A tool rejected its arguments before doing any work."""


def sanitize_arguments(arguments: dict, schema: dict) -> tuple[dict, list[str]]:
    """Convert explicit form values, never invent missing patient measurements."""
    cleaned, changes = dict(arguments), []
    for name, field in schema.get('properties', {}).items():
        if name not in cleaned:
            if name not in schema.get('required', []) and 'default' in field:
                cleaned[name] = field['default']
            continue
        value = cleaned[name]
        if isinstance(value, str) and field.get('type') in {'integer', 'number'}:
            try:
                number = float(value.strip().replace(',', '.'))
                if field['type'] == 'integer' and not number.is_integer():
                    raise ValueError('not integer')
                cleaned[name] = int(number) if field['type'] == 'integer' else number
                changes.append(f'{name}: числовая строка приведена к числу')
            except (ValueError, OverflowError):
                raise MCPValidationError(f'Поле {_field_label(name)} должно быть числом')
        elif isinstance(value, str) and field.get('type') == 'boolean' and value.lower() in {'true', 'false'}:
            cleaned[name] = value.lower() == 'true'
            changes.append(f'{name}: приведено к логическому значению')
    return cleaned, changes


class RecordedStream:
    def __init__(self, stream, trace, direction):
        self.stream, self.trace, self.direction = stream, trace, direction

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def record(self, value):
        message = getattr(value, 'message', None)
        if message is not None:
            self.trace.append({'direction': self.direction, 'packet': message.model_dump(mode='json', exclude_none=True)})

    async def send(self, value):
        self.record(value)
        await self.stream.send(value)

    async def receive(self):
        value = await self.stream.receive()
        self.record(value)
        return value

    def __aiter__(self):
        return self

    async def __anext__(self):
        import anyio
        try:
            return await self.receive()
        except anyio.EndOfStream:
            raise StopAsyncIteration

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


@asynccontextmanager
async def recorded_transport(server, trace):
    from mcp.client.stdio import stdio_client
    from mcp.client.sse import sse_client
    from mcp.client.streamable_http import streamable_http_client
    transport = stdio_client(server) if isinstance(server, StdioServerParameters) else sse_client(server) if str(server).rstrip('/').endswith('/sse') else streamable_http_client(server)
    async with transport as streams:
        yield RecordedStream(streams[0], trace, 'response'), RecordedStream(streams[1], trace, 'request')


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump(mode="json"))
    if hasattr(value, "dict"):
        return _jsonable(value.dict())
    if hasattr(value, "__dict__"):
        return _jsonable(value.__dict__)
    return str(value)


def _tool_name(tool: Any) -> str:
    return str(getattr(tool, "name", ""))


def _tool_schema(tool: Any) -> dict[str, Any]:
    schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None) or {}
    return _jsonable(schema)


def _field_label(name: str) -> str:
    return {"drug": "Препарат", "gene": "Ген", "query": "Поисковый запрос", "drug_name": "Название препарата"}.get(name, name.replace("_", " "))


def _trace_request(trace: list[dict[str, Any]], request_id: int, method: str, params: dict[str, Any]) -> None:
    trace.append({"direction": "request", "packet": {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}})


def _trace_response(trace: list[dict[str, Any]], request_id: int, result: Any) -> None:
    trace.append({"direction": "response", "packet": {"jsonrpc": "2.0", "id": request_id, "result": _jsonable(result)}})


def _trace_error(trace: list[dict[str, Any]], request_id: int, message: str) -> None:
    trace.append({"direction": "response", "packet": {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": message}}})


def _is_port_open(url: str) -> bool:
    try:
        host_port = url.split("://", 1)[1].split("/", 1)[0]
        host, port = host_port.rsplit(":", 1)
        with socket.create_connection((host, int(port)), timeout=0.2):
            return True
    except (OSError, ValueError, IndexError):
        return False


def ensure_local_network_server() -> None:
    """Start the local MCP daemon on demand for the browser demonstration."""
    global _network_process
    if _is_port_open(LOCAL_HTTP_URL):
        return
    with _process_lock:
        if _is_port_open(LOCAL_HTTP_URL):
            return
        _network_process = subprocess.Popen(
            [sys.executable, "-m", "mcp_servers.network_server"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(30):
            if _is_port_open(LOCAL_HTTP_URL):
                return
            if _network_process.poll() is not None:
                raise MCPClientError("Локальный MCP-сервер завершился до открытия порта 8000.")
            time.sleep(0.1)
        raise MCPClientError("Локальный MCP-сервер не ответил за 3 секунды.")


def _source_server(source: str) -> Any:
    if source == "stdio":
        return StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_servers.stdio_server"],
            cwd=str(ROOT),
        )
    if source == "network":
        ensure_local_network_server()
        return LOCAL_HTTP_URL
    if source == "external":
        if EXTERNAL_HTTP_URL:
            return EXTERNAL_HTTP_URL
        # Glama lists this public Streamable HTTP medical endpoint alongside
        # the medical-mcp package. It is used only when explicitly enabled.
        glama_url = os.environ.get('PHARMACOGEN_GLAMA_MCP_URL', '').strip()
        if glama_url:
            return glama_url
        external_command = os.environ.get("PHARMACOGEN_EXTERNAL_MCP_COMMAND", "").strip()
        if external_command:
            parts = shlex.split(external_command)
            if not parts:
                raise MCPClientError("PHARMACOGEN_EXTERNAL_MCP_COMMAND пуст.")
            return StdioServerParameters(command=parts[0], args=parts[1:])
        installed = ROOT / 'node_modules' / 'medical-mcp' / 'build' / 'index.js'
        if installed.is_file():
            return StdioServerParameters(command=shutil_which('node') or 'node', args=['-e', 'console.log=console.error; import(require("url").pathToFileURL(process.argv[1]))', str(installed)], cwd=str(ROOT))
        if not shutil_which("npx"):
            raise MCPClientError("Для внешнего режима нужен npx или PHARMACOGEN_EXTERNAL_MCP_URL.")
        # The published package exposes an ESM entrypoint without a portable
        # shebang. Launch it through Node so the external process remains a
        # genuine MCP server instead of a shell script invocation.
        return StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "--package=medical-mcp",
                "sh",
                "-c",
                'node -e "console.log=console.error; import(require(\'url\').pathToFileURL(process.argv[1]))" "$(command -v medical-mcp)"',
            ],
        )
    raise MCPClientError(f"Неизвестный источник MCP: {source}")


def shutil_which(command: str) -> str | None:
    for folder in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(folder) / command
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


async def _invoke_once(source: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    trace: list[dict[str, Any]] = []
    server = _source_server(source)
    client_mode = "legacy" if source == "external" else "auto"
    failure: MCPClientError | None = None
    response_payload: dict[str, Any] | None = None
    async with Client(recorded_transport(server, trace), read_timeout_seconds=12 if source == 'external' else 40, mode='legacy') as client:
        request_id = 1
        request_id += 1
        tools_result = await client.list_tools()
        tools = list(getattr(tools_result, "tools", []) or [])
        selected = next((tool for tool in tools if _tool_name(tool) == tool_name), None)
        if selected is None:
            available = ", ".join(_tool_name(tool) for tool in tools[:20]) or "нет инструментов"
            failure = MCPClientError(f"Инструмент {tool_name} не найден. Доступны: {available}")
        else:
            schema = _tool_schema(selected)
            arguments, adjustments = sanitize_arguments(arguments, schema)
            missing = [name for name in schema.get("required", []) if arguments.get(name) is None or str(arguments.get(name, "")).strip() == ""]
            if missing:
                _trace_error(trace, request_id, f"Заполните: {', '.join(_field_label(name) for name in missing)}")
                failure = MCPValidationError(f"Заполните: {', '.join(_field_label(name) for name in missing)}")
            else:
                request_id += 1
                try:
                    result = await client.call_tool(tool_name, arguments)
                except ValueError as exc:
                    _trace_error(trace, request_id, str(exc))
                    failure = MCPValidationError("Проверьте обязательные параметры инструмента.")
                else:
                    if getattr(result, "is_error", False):
                        content = getattr(result, "content", []) or []
                        raw_message = next((getattr(item, "text", "") for item in content if getattr(item, "text", "")), "")
                        _trace_error(trace, request_id, raw_message or "Инструмент отклонил параметры.")
                        if "validation" in raw_message.casefold() or "should have at least" in raw_message.casefold():
                            failure = MCPValidationError("Проверьте обязательные параметры инструмента.")
                        else:
                            failure = MCPClientError(raw_message or "Инструмент отклонил параметры.")
                    else:
                        response_payload = {
                            "source": source,
                            "tool": {"name": _tool_name(selected), "description": getattr(selected, "description", ""), "inputSchema": schema},
                            "result": _jsonable(result),
                            "trace": trace,
                            "server": _jsonable(client.server_info),
                            "adjustments": adjustments,
                            "transport": 'stdio' if isinstance(server, StdioServerParameters) else 'sse' if str(server).rstrip('/').endswith('/sse') else 'streamable-http',
                        }
    if failure:
        raise failure
    if response_payload is None:
        raise MCPClientError("MCP не вернул результат.")
    return response_payload


def _cache_key(source: str, tool_name: str, arguments: dict[str, Any]) -> str:
    return json.dumps([source, tool_name, arguments], ensure_ascii=False, sort_keys=True)


def _cacheable_response(response: dict[str, Any]) -> bool:
    result = response.get("result") or {}
    if not isinstance(result, dict) or result.get("isError") or result.get("is_error"):
        return False
    structured = result.get("structuredContent") or result.get("structured_content")
    if not isinstance(structured, dict):
        for block in result.get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    structured = json.loads(block.get("text", ""))
                except (TypeError, ValueError):
                    pass
                break
    details = structured.get("details", {}) if isinstance(structured, dict) else {}
    return not ((isinstance(structured, dict) and structured.get("status") in {"error", "unavailable"}) or (isinstance(details, dict) and details.get("status") in {"error", "unavailable"}))


async def _invoke_with_retry(source: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    key = _cache_key(source, tool_name, arguments)
    with _cache_lock:
        cached = _cache.get(key)
        if cached and cached[0] > time.monotonic():
            result = dict(cached[1])
            result["cache_hit"] = True
            return result
    last_error: Exception | None = None
    for attempt in range(1 if source == 'external' else 2):
        try:
            result = await asyncio.wait_for(_invoke_once(source, tool_name, arguments), timeout=15 if source == 'external' else 50)
            result["cache_hit"] = False
            if _cacheable_response(result):
                with _cache_lock:
                    _cache[key] = (time.monotonic() + CACHE_TTL_SECONDS, result)
            return result
        except MCPValidationError:
            raise
        except (asyncio.TimeoutError, OSError, MCPClientError) as exc:
            last_error = exc
            if attempt == 0:
                await asyncio.sleep(0.25)
    raise MCPClientError(f"Источник MCP недоступен после 2 попыток: {last_error}") from last_error


def call_mcp_tool(source: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Synchronously bridge the browser handler to the asynchronous MCP client."""
    return asyncio.run(_invoke_with_retry(source, tool_name, arguments))


async def _check_connection(source: str) -> dict[str, Any]:
    server = _source_server(source)
    trace = []
    async with Client(recorded_transport(server, trace), read_timeout_seconds=12, mode='legacy') as client:
        result = await client.list_tools()
        return {"source": source, "server": _jsonable(client.server_info), "tools": [{"name": _tool_name(tool), "description": str(getattr(tool, "description", "") or ""), 'inputSchema': _tool_schema(tool)} for tool in result.tools], 'trace': trace, 'external_connection': 'remote' if source == 'external' and isinstance(server, str) else 'vendor-package' if source == 'external' else None}


def check_mcp_connection(source: str) -> dict[str, Any]:
    async def run() -> dict[str, Any]:
        return await asyncio.wait_for(_check_connection(source), timeout=15)
    try:
        return asyncio.run(run())
    except Exception as exc:
        raise MCPClientError(f"Не удалось подключиться к MCP: {exc}") from exc


def list_mcp_catalog() -> dict[str, Any]:
    """Return schemas used by the dynamic form before a tool is called."""
    from mcp_servers.pharmacogenetic_tools import list_pharmacogenetic_tools

    return {
        "sources": [
            {"id": "stdio", "title": "Локальный stdio", "description": "Дочерний Python-процесс и stdin/stdout JSON-RPC."},
            {"id": "network", "title": "Локальный сетевой", "description": "MCP Streamable HTTP на http://127.0.0.1:8000/mcp; три аналитических инструмента."},
            {"id": "external", "title": "Внешний medical-mcp", "description": "Пакет из каталога Glama с FDA, PubMed и RxNorm."},
        ],
        "local_tools": [
            *[{"name": name, "title": title, "category": "проверка исследования", "inputSchema": {"type": "object", "properties": {"report": {"type": "object"}, "dossier": {"type": "object"}}, "required": ["report", "dossier"]}} for name, title in [("audit_research_tool", "Проверка полноты досье"), ("match_variant_tool", "Сопоставление варианта"), ("plan_review_tool", "План проверки"), ("inspect_publications_tool", "Разбор публикаций"), ("inspect_clinvar_tool", "Разбор ClinVar")]],
            {"name": "search_faers_tool", "title": "Поиск FAERS", "category": "источники", "inputSchema": {"type": "object", "properties": {"drug": {"type": "string"}}, "required": ["drug"]}},
            {"name": "search_clinvar_tool", "title": "Поиск ClinVar", "category": "источники", "inputSchema": {"type": "object", "properties": {"drug": {"type": "string"}, "gene": {"type": "string"}, "variant": {"type": "string"}}, "required": ["drug", "gene"]}},
            {"name": "search_cpic_guidelines_tool", "title": "Поиск рекомендаций CPIC", "category": "источники", "inputSchema": {"type": "object", "properties": {"drug": {"type": "string"}, "gene": {"type": "string"}}, "required": ["drug", "gene"]}},
            {"name": "search_clinpgx_annotations_tool", "title": "Поиск аннотаций ClinPGx", "category": "источники", "inputSchema": {"type": "object", "properties": {"drug": {"type": "string"}, "gene": {"type": "string"}, "variant": {"type": "string"}}, "required": ["drug", "gene"]}},
        ] + [
            {"name": f"{item['name']}_tool", "title": item["title"], "category": item["category"], "inputSchema": {"type": "object", "properties": item["parameters"], "required": item.get("required", [])}, "source": item["source"]}
            for item in list_pharmacogenetic_tools()
        ],
        "external_tools": [
            {"name": "search-medical-literature", "title": "Поиск медицинской литературы", "category": "внешний источник", "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "Название препарата, гена или клинический вопрос"}, "max_results": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5}}, "required": ["query"]}, "source": "https://glama.ai/mcp/servers/JamesANZ/medical-mcp"},
            {"name": "get-drug-details", "title": "Данные о препарате FDA", "category": "внешний источник", "inputSchema": {"type": "object", "properties": {"drug_name": {"type": "string"}}, "required": ["drug_name"]}, "source": "https://glama.ai/mcp/servers/JamesANZ/medical-mcp"},
        ],
    }
