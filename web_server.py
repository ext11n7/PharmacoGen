from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from agents import MCPClinVarClient, MCPFaersClient, run_investigation
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


def _extract_mcp_result(payload: dict[str, object]) -> dict[str, object]:
    result = payload.get("result") or {}
    if not isinstance(result, dict):
        return {"summary": "MCP вернул неожиданный формат ответа."}
    structured = result.get("structuredContent") or result.get("structured_content")
    if isinstance(structured, dict):
        return structured
    for item in result.get("content", []) if isinstance(result.get("content"), list) else []:
        if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
            try:
                parsed = json.loads(str(item["text"]))
            except json.JSONDecodeError:
                return {"summary": str(item["text"])}
            return parsed if isinstance(parsed, dict) else {"summary": str(parsed)}
    return result


def _report_mcp_arguments(report: dict[str, object]) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    query = report.get("normalized_query") or report.get("query") or {}
    faers = report.get("faers") or {}
    clinvar = report.get("clinvar") or {}
    if not isinstance(query, dict) or not isinstance(faers, dict) or not isinstance(clinvar, dict):
        raise ValueError("Отчёт исследования имеет неполный формат")
    drug, gene = str(query.get("drug", "")).strip(), str(query.get("gene", "")).strip()
    if not drug or not gene:
        raise ValueError("В отчёте нет препарата или гена")
    reactions = faers.get("top_reactions") if isinstance(faers.get("top_reactions"), list) else []
    records = clinvar.get("records") if isinstance(clinvar.get("records"), list) else []
    synthesis = {
        "drug": drug,
        "gene": gene,
        "variant": str(query.get("variant", "")),
        "faers_available": faers.get("status") == "ok",
        "faers_reports": int(faers.get("total_reports") or 0),
        "faers_serious_rate": float(faers.get("serious_rate") or 0),
        "clinvar_available": clinvar.get("status") == "ok",
        "clinvar_records": int(clinvar.get("total_records") or 0),
        "clinvar_pathogenic_records": int(clinvar.get("pathogenic_records") or 0),
        "top_reaction": str(reactions[0].get("term", "")) if reactions and isinstance(reactions[0], dict) else "",
    }
    audit = {
        "faers_available": synthesis["faers_available"],
        "faers_reports": synthesis["faers_reports"],
        "clinvar_available": synthesis["clinvar_available"],
        "clinvar_records": synthesis["clinvar_records"],
        "has_variant": bool(synthesis["variant"]),
        "has_source_links": bool(faers.get("source") and clinvar.get("source")),
    }
    return synthesis, audit, [item for item in records[:3] if isinstance(item, dict)]


def build_mcp_dossier(report: dict[str, object], source: str = "stdio") -> dict[str, object]:
    """Run a multi-step MCP workflow over one already collected report."""
    if source not in {"stdio", "network"}:
        raise ValueError("Для досье выберите локальный stdio или локальный сетевой MCP")
    synthesis_arguments, audit_arguments, records = _report_mcp_arguments(report)
    calls: list[dict[str, object]] = []

    def run_stage(tool: str, arguments: dict[str, object], title: str) -> dict[str, object]:
        try:
            response = call_mcp_tool(source, tool, arguments)
            calls.append({"title": title, "tool": tool, "status": "done", "trace": response.get("trace", [])})
            return _extract_mcp_result(response)
        except MCPClientError as exc:
            calls.append({"title": title, "tool": tool, "status": "error", "error": str(exc), "trace": []})
            return {"summary": "Этап не выполнен", "error": str(exc), "next_steps": []}

    synthesis = run_stage("synthesize_evidence_tool", synthesis_arguments, "Синтез источников")
    audit = run_stage("audit_evidence_quality_tool", audit_arguments, "Контроль качества")
    literature = run_stage(
        "search_pharmacogenetic_literature_tool",
        {"drug": synthesis_arguments["drug"], "gene": synthesis_arguments["gene"], "variant": synthesis_arguments["variant"], "max_results": 5},
        "Поиск публикаций",
    )
    prioritized = []
    for index, record in enumerate(records, start=1):
        variant = str(record.get("title") or record.get("accession") or synthesis_arguments["variant"] or "")
        prioritized.append(run_stage(
            "prioritize_variant_review_tool",
            {
                "drug": synthesis_arguments["drug"],
                "gene": synthesis_arguments["gene"],
                "variant": variant,
                "classification": str(record.get("classification", "")),
                "review_status": str(record.get("review_status", "")),
                "traits": ", ".join(str(item) for item in record.get("traits", []) if item),
            },
            f"Приоритет варианта {index}",
        ))
    literature_details = literature.get("details", {}) if isinstance(literature, dict) else {}
    literature_records = literature_details.get("records", []) if isinstance(literature_details, dict) else []
    literature_titles = "; ".join(str(item.get("title", "")) for item in literature_records[:3] if isinstance(item, dict) and item.get("title"))
    hypotheses = run_stage(
        "formulate_hypotheses_tool",
        {
            "drug": synthesis_arguments["drug"],
            "gene": synthesis_arguments["gene"],
            "variant": synthesis_arguments["variant"],
            "faers_reports": synthesis_arguments["faers_reports"],
            "faers_serious_rate": synthesis_arguments["faers_serious_rate"],
            "clinvar_records": synthesis_arguments["clinvar_records"],
            "clinvar_pathogenic_records": synthesis_arguments["clinvar_pathogenic_records"],
            "literature_count": min(int(literature_details.get("total", 0) or 0), 1_000_000) if isinstance(literature_details, dict) else 0,
            "top_reaction": synthesis_arguments["top_reaction"],
            "literature_titles": literature_titles[:240],
        },
        "Формирование гипотез",
    )
    next_steps = list(synthesis.get("next_steps", [])) + list(audit.get("next_steps", []))
    next_steps.extend(literature.get("next_steps", []))
    for item in prioritized:
        next_steps.extend(item.get("next_steps", []))
    next_steps.extend(hypotheses.get("next_steps", []))
    unique_steps = list(dict.fromkeys(str(item) for item in next_steps if item))[:8]
    return {
        "status": "ok",
        "workflow": {"title": "Исследовательское досье", "stages": calls, "completed": sum(stage["status"] == "done" for stage in calls), "total": len(calls)},
        "query": synthesis_arguments,
        "synthesis": synthesis,
        "quality": audit,
        "literature": literature,
        "prioritized_variants": prioritized,
        "hypotheses": hypotheses,
        "next_steps": unique_steps,
        "limitations": [
            "MCP анализирует собранный срез и не заменяет чтение исходных записей.",
            "FAERS содержит спонтанные сообщения: их количество не равно частоте и не доказывает причинность.",
            "ClinVar-классификация не доказывает фармакогенетический эффект без дополнительного контекста.",
        ],
        "trace": [packet for stage in calls for packet in stage.get("trace", [])],
    }


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
        if path == "/api/analysis":
            try:
                from mcp_servers.research_summary import create_summary
                length = int(self.headers.get("Content-Length", "0"))
                if length > 200_000:
                    raise ValueError("Отчёт слишком велик")
                payload = json.loads(self.rfile.read(length) or b"{}")
                report, dossier = payload.get("report"), payload.get("dossier")
                if not isinstance(report, dict) or not isinstance(dossier, dict):
                    raise ValueError("Сначала соберите исследование")
                self._send(json.dumps(create_summary(report, dossier), ensure_ascii=False).encode(), "application/json; charset=utf-8")
            except (ValueError, TypeError) as exc:
                self._send(json.dumps({"error": str(exc)}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 400)
            return
        if path == "/api/mcp/check":
            try:
                from mcp_clients.router import check_mcp_connection
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length) or b"{}")
                source = str(payload.get("source", ""))
                if source not in {"stdio", "network", "external"}:
                    raise ValueError("Выберите источник MCP")
                self._send(json.dumps(check_mcp_connection(source), ensure_ascii=False).encode(), "application/json; charset=utf-8")
            except (MCPClientError, ValueError) as exc:
                self._send(json.dumps({"error": str(exc)}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 502)
            return
        if path == "/api/mcp/call":
            self._handle_mcp_call()
            return
        if path == "/api/mcp/dossier":
            self._handle_mcp_dossier()
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
            report = run_investigation(drug, gene, clients={"faers": MCPFaersClient(), "clinvar": MCPClinVarClient()}, variant=variant)
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

    def _handle_mcp_dossier(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            report = payload.get("report")
            source = str(payload.get("source", "stdio")).strip()
            if not isinstance(report, dict):
                raise ValueError("Передайте готовый отчёт исследования")
            if source not in {"stdio", "network"}:
                raise ValueError("Выберите локальный MCP-транспорт")
            query, _, _ = _report_mcp_arguments(report)
            try:
                response = call_mcp_tool(source, "search_pharmacogenetic_literature_tool", {"drug": query["drug"], "gene": query["gene"], "variant": query["variant"], "max_results": 5})
                literature = _extract_mcp_result(response)
                trace = list(response.get("trace", []))
            except MCPClientError as exc:
                literature = {"details": {"status": "unavailable", "error": str(exc), "records": []}}
                trace = []
            try:
                cpic_response = call_mcp_tool(source, "search_cpic_guidelines_tool", {"drug": query["drug"], "gene": query["gene"]})
                cpic = _extract_mcp_result(cpic_response)
                trace.extend(cpic_response.get("trace", []))
            except MCPClientError as exc:
                cpic = {"status": "unavailable", "error": str(exc), "records": []}
            try:
                annotation_response = call_mcp_tool(source, "search_clinpgx_annotations_tool", {"drug": query["drug"], "gene": query["gene"], "variant": query["variant"]})
                clinpgx = _extract_mcp_result(annotation_response)
                trace.extend(annotation_response.get("trace", []))
            except MCPClientError as exc:
                clinpgx = {"status": "unavailable", "error": str(exc), "records": []}
            dossier = {"status": "ok", "literature": literature, "cpic": cpic, "clinpgx": clinpgx, "trace": trace, "transport": source}
            self._send(json.dumps(dossier, ensure_ascii=False).encode(), "application/json; charset=utf-8")
        except ValueError as exc:
            self._send(json.dumps({"error": str(exc)}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 400)
        except MCPClientError as exc:
            self._send(json.dumps({"error": str(exc)}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 502)
        except Exception as exc:
            self._send(json.dumps({"error": f"Не удалось собрать MCP-досье: {exc}"}, ensure_ascii=False).encode(), "application/json; charset=utf-8", 502)

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
