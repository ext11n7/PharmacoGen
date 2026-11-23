import asyncio
import sys

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from mcp_servers.pharmacogenetic_tools import audit_evidence_quality, formulate_hypotheses, prioritize_variant_review, synthesize_evidence
from mcp_clients.router import MCPValidationError, _cacheable_response, call_mcp_tool, list_mcp_catalog


def test_unavailable_source_is_not_cached():
    unavailable = {"result": {"structuredContent": {"details": {"status": "unavailable", "error": "HTTP 429"}}}}
    available = {"result": {"structuredContent": {"details": {"status": "ok", "total": 0}}}}
    assert not _cacheable_response(unavailable)
    assert _cacheable_response(available)


def test_mcp_tools_analyze_existing_evidence():
    synthesis = synthesize_evidence(
        "warfarin", "cyp2c9", "rs1799853", True, 120, 0.25, True, 8, 2, "Haemorrhage",
    )
    assert synthesis["details"]["priority"] == "не оценён"
    assert synthesis["details"]["available_sources"] == 2
    assert synthesis["next_steps"]
    assert prioritize_variant_review("warfarin", "CYP2C9", "rs1799853", "Pathogenic", "criteria provided", "drug response")["details"]["priority"] == "высокий"
    audit = audit_evidence_quality(True, 120, True, 8, True, True)
    assert audit["details"]["quality_score"] == 100


def test_mcp_catalog_contains_useful_project_tools():
    catalog = list_mcp_catalog()
    assert {source["id"] for source in catalog["sources"]} == {"stdio", "network", "external"}
    assert {tool["name"] for tool in catalog["local_tools"]} == {
        "search_faers_tool",
        "search_clinvar_tool",
        "synthesize_evidence_tool",
        "prioritize_variant_review_tool",
        "audit_evidence_quality_tool",
        "search_pharmacogenetic_literature_tool",
        "formulate_hypotheses_tool",
    }
    assert any(tool["name"] == "search-medical-literature" for tool in catalog["external_tools"])
    clinvar = next(tool for tool in catalog["local_tools"] if tool["name"] == "search_clinvar_tool")
    assert clinvar["inputSchema"]["required"] == ["drug", "gene"]


def test_router_rejects_empty_tool_call_before_transport():
    try:
        call_mcp_tool("stdio", "synthesize_evidence_tool", {})
    except MCPValidationError as exc:
        assert str(exc) == "Заполните: Препарат, Ген"
    else:
        raise AssertionError("Пустой вызов должен быть отклонён")


def test_hypotheses_are_explicit_and_actionable():
    result = formulate_hypotheses("warfarin", "CYP2C9", "rs1799853", 120, 0.2, 8, 2, 40, "Haemorrhage", "Warfarin dose requirements")
    assert len(result["details"]["hypotheses"]) == 3
    assert result["details"]["hypotheses"][0]["next_step"]
    assert "гипотез" in result["summary"]


def test_stdio_server_exposes_analytical_tools():
    async def run() -> None:
        server = StdioServerParameters(command=sys.executable, args=["-m", "mcp_servers.stdio_server"], cwd=".")
        async with Client(server, read_timeout_seconds=5) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            assert {"synthesize_evidence_tool", "prioritize_variant_review_tool", "audit_evidence_quality_tool", "search_pharmacogenetic_literature_tool", "formulate_hypotheses_tool", "list_pharmacogenetic_tools_tool"} <= names
            result = await client.call_tool("synthesize_evidence_tool", {"drug": "warfarin", "gene": "CYP2C9", "faers_available": True, "faers_reports": 10, "clinvar_available": True, "clinvar_records": 2, "clinvar_pathogenic_records": 1})
            assert result.is_error is False
            assert "проверки" in result.content[0].text

    asyncio.run(run())
