"""Local MCP server using the stdio transport."""

from __future__ import annotations

import logging

from mcp.server import MCPServer

from .pharmacogenetic_tools import (
    DrugName,
    GeneSymbol,
    OptionalText,
    Rate,
    ReportCount,
    audit_evidence_quality,
    list_pharmacogenetic_tools,
    prioritize_variant_review,
    synthesize_evidence,
)


logging.basicConfig(level=logging.INFO, format="[stdio-mcp] %(message)s")
mcp = MCPServer(
    "pharmacogen-stdio",
    description="Аналитические инструменты PharmacoGen для уже собранных доказательств",
    instructions="Передайте MCP сводку FAERS и ClinVar после выполнения основного исследования.",
    version="1.1.0",
)


@mcp.tool()
def synthesize_evidence_tool(
    drug: DrugName,
    gene: GeneSymbol,
    variant: OptionalText = "",
    faers_available: bool = False,
    faers_reports: ReportCount = 0,
    faers_serious_rate: Rate = 0,
    clinvar_available: bool = False,
    clinvar_records: ReportCount = 0,
    clinvar_pathogenic_records: ReportCount = 0,
    top_reaction: OptionalText = "",
) -> dict:
    """Сопоставить сводки FAERS и ClinVar и предложить следующий шаг проверки."""
    return synthesize_evidence(drug, gene, variant, faers_available, faers_reports, faers_serious_rate, clinvar_available, clinvar_records, clinvar_pathogenic_records, top_reaction)


@mcp.tool()
def prioritize_variant_review_tool(
    drug: DrugName,
    gene: GeneSymbol,
    variant: OptionalText = "",
    classification: OptionalText = "",
    review_status: OptionalText = "",
    traits: OptionalText = "",
) -> dict:
    """Определить приоритет ручной проверки варианта ClinVar."""
    return prioritize_variant_review(drug, gene, variant, classification, review_status, traits)


@mcp.tool()
def audit_evidence_quality_tool(
    faers_available: bool = False,
    faers_reports: ReportCount = 0,
    clinvar_available: bool = False,
    clinvar_records: ReportCount = 0,
    has_variant: bool = False,
    has_source_links: bool = False,
) -> dict:
    """Проверить полноту данных перед исследовательским выводом."""
    return audit_evidence_quality(faers_available, faers_reports, clinvar_available, clinvar_records, has_variant, has_source_links)


@mcp.tool()
def list_pharmacogenetic_tools_tool() -> list[dict]:
    """Показать каталог аналитических инструментов PharmacoGen."""
    return list_pharmacogenetic_tools()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
