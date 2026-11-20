import asyncio
import sys

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters

from mcp_servers.pharmacogenetic_tools import (
    build_evidence_query,
    classify_variant_for_review,
    compare_source_signals,
    normalize_pharmacogenetic_query,
)
from mcp_clients.router import list_mcp_catalog


def test_pharmacogenetic_tools_prepare_project_evidence():
    normalized = normalize_pharmacogenetic_query(" warfarin ", "cyp2c9", "rs1799853")
    assert normalized["details"]["gene"] == "CYP2C9"
    assert normalized["details"]["faers_query"] == "warfarin CYP2C9"
    plan = build_evidence_query("warfarin", "CYP2C9", "rs1799853", 5)
    assert {item["source"] for item in plan["details"]["requests"]} == {"FAERS", "ClinVar", "PubMed", "FDA"}
    assert classify_variant_for_review("CYP2C9", "rs1799853")["details"]["notation"] == "идентификатор dbSNP"
    assert compare_source_signals(4, 2, 1, 3)["details"]["comparison_state"] == "есть сигналы в нескольких источниках"


def test_mcp_catalog_contains_dynamic_sources_and_forms():
    catalog = list_mcp_catalog()
    assert {source["id"] for source in catalog["sources"]} == {"stdio", "network", "external"}
    assert {tool["name"] for tool in catalog["local_tools"]} == {
        "normalize_pharmacogenetic_query_tool",
        "build_evidence_query_tool",
        "classify_variant_for_review_tool",
        "compare_source_signals_tool",
    }
    assert any(tool["name"] == "search-medical-literature" for tool in catalog["external_tools"])


def test_stdio_server_exposes_mcp_tools_and_calculates():
    async def run() -> None:
        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_servers.stdio_server"],
            cwd=".",
        )
        async with Client(server, read_timeout_seconds=5) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            assert {"normalize_pharmacogenetic_query_tool", "build_evidence_query_tool", "classify_variant_for_review_tool", "compare_source_signals_tool", "list_pharmacogenetic_tools_tool"} <= names
            result = await client.call_tool("normalize_pharmacogenetic_query_tool", {"drug": "warfarin", "gene": "CYP2C9", "variant": "rs1799853"})
            assert result.is_error is False
            assert "CYP2C9" in result.content[0].text

    asyncio.run(run())
