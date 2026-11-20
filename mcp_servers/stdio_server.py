"""Local MCP server using the stdio transport.

Run with: python -m mcp_servers.stdio_server
Only MCP messages go to stdout. Logs are sent to stderr.
"""

from __future__ import annotations

import logging

from mcp.server import MCPServer

from .pharmacogenetic_tools import (
    build_evidence_query,
    classify_variant_for_review,
    compare_source_signals,
    GeneSymbol,
    DrugName,
    EvidenceCount,
    MaxResults,
    VariantName,
    list_pharmacogenetic_tools,
    normalize_pharmacogenetic_query,
)


logging.basicConfig(level=logging.INFO, format="[stdio-mcp] %(message)s")
mcp = MCPServer(
    "pharmacogen-stdio",
    description="Локальные инструменты подготовки фармакогенетического поиска",
    instructions="Используйте tools/list для каталога и tools/call для подготовки доказательств.",
    version="1.0.0",
)


@mcp.tool()
def normalize_pharmacogenetic_query_tool(drug: DrugName, gene: GeneSymbol, variant: VariantName = "") -> dict:
    """Нормализовать препарат, ген и вариант для поиска."""
    return normalize_pharmacogenetic_query(drug, gene, variant)


@mcp.tool()
def build_evidence_query_tool(
    drug: DrugName,
    gene: GeneSymbol,
    variant: VariantName = "",
    max_results: MaxResults = 5,
) -> dict:
    """Собрать поисковые задания для FAERS, ClinVar, PubMed и FDA."""
    return build_evidence_query(drug, gene, variant, max_results)


@mcp.tool()
def classify_variant_for_review_tool(gene: GeneSymbol, variant: VariantName) -> dict:
    """Подготовить формат варианта к проверке в ClinVar."""
    return classify_variant_for_review(gene, variant)


@mcp.tool()
def compare_source_signals_tool(
    faers_reports: EvidenceCount = 0,
    clinvar_records: EvidenceCount = 0,
    pathogenic_records: EvidenceCount = 0,
    literature_hits: EvidenceCount = 0,
) -> dict:
    """Сопоставить количество сигналов из уже собранных источников."""
    return compare_source_signals(faers_reports, clinvar_records, pathogenic_records, literature_hits)


@mcp.tool()
def list_pharmacogenetic_tools_tool() -> list[dict]:
    """Показать каталог локальных инструментов PharmacoGen."""
    return list_pharmacogenetic_tools()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
