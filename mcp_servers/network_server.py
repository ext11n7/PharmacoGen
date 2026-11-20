"""Local network MCP server using Streamable HTTP on port 8000."""

from __future__ import annotations

import logging
import os

from mcp.server import MCPServer

from .pharmacogenetic_tools import (
    build_evidence_query,
    classify_variant_for_review,
    compare_source_signals,
    DrugName,
    EvidenceCount,
    GeneSymbol,
    MaxResults,
    VariantName,
    list_pharmacogenetic_tools,
    normalize_pharmacogenetic_query,
)


logging.basicConfig(level=logging.INFO, format="[network-mcp] %(message)s")
mcp = MCPServer(
    "pharmacogen-network",
    description="Локальный каталог фармакогенетических инструментов PharmacoGen",
    instructions="Сначала вызовите tools/list, затем передайте препарат, ген и вариант в tools/call.",
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
    port = int(os.environ.get("PHARMACOGEN_MCP_PORT", "8000"))
    host = os.environ.get("PHARMACOGEN_MCP_HOST", "127.0.0.1")
    mcp.run(transport="streamable-http", host=host, port=port, streamable_http_path="/mcp")


if __name__ == "__main__":
    main()
