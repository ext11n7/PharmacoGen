import asyncio
import sys

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters

from mcp_servers.clinical_tools import calculate_bmi, calculate_gcs, calculate_map
from mcp_clients.router import list_mcp_catalog


def test_clinical_tools_validate_ranges():
    assert calculate_bmi(70, 175)["value"] == 22.9
    assert calculate_gcs(4, 5, 6)["value"] == 15
    with pytest.raises(ValueError, match="должно быть меньше"):
        calculate_map(100, 120)


def test_mcp_catalog_contains_dynamic_sources_and_forms():
    catalog = list_mcp_catalog()
    assert {source["id"] for source in catalog["sources"]} == {"stdio", "network", "external"}
    assert any(tool["name"] == "calculate_chadsvasc_tool" for tool in catalog["local_tools"])
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
            assert {"calculate_bmi_tool", "calculate_ckd_epi_tool", "calculate_chadsvasc_tool", "list_calculators_tool"} <= names
            result = await client.call_tool("calculate_bmi_tool", {"weight_kg": 70, "height_cm": 175})
            assert result.is_error is False
            assert "22.9" in result.content[0].text

    asyncio.run(run())
