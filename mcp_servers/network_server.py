"""Local MCP server using Streamable HTTP."""

from __future__ import annotations

import logging
import os

from mcp.server import MCPServer

from .pharmacogenetic_tools import (
    DrugName,
    GeneSymbol,
    OptionalText,
    Rate,
    ReportCount,
    audit_evidence_quality,
    formulate_hypotheses,
    list_pharmacogenetic_tools,
    prioritize_variant_review,
    search_pharmacogenetic_literature,
    synthesize_evidence,
)


logging.basicConfig(level=logging.INFO, format="[network-mcp] %(message)s")
mcp = MCPServer(
    "pharmacogen-network",
    description="Сетевой аналитический MCP-сервер PharmacoGen",
    instructions="Передайте MCP сводку FAERS и ClinVar после выполнения основного исследования.",
    version="1.1.0",
)


@mcp.tool()
def audit_research_tool(report: dict, dossier: dict) -> dict:
    """Проверить полноту уже собранного исследовательского досье."""
    from .evidence_tools import audit_research
    return audit_research(report, dossier)


@mcp.tool()
def match_variant_tool(report: dict, dossier: dict) -> dict:
    """Сопоставить обозначение варианта с загруженными аннотациями ClinPGx."""
    from .evidence_tools import match_variant
    return match_variant(report, dossier)


@mcp.tool()
def plan_review_tool(report: dict, dossier: dict) -> dict:
    """Составить план дальнейшей проверки собранных данных."""
    from .evidence_tools import plan_review
    return plan_review(report, dossier)


@mcp.tool()
def inspect_publications_tool(report: dict, dossier: dict) -> dict:
    """Показать типы и наличие аннотаций найденных публикаций."""
    from .evidence_tools import inspect_publications
    return inspect_publications(report, dossier)


@mcp.tool()
def inspect_clinvar_tool(report: dict, dossier: dict) -> dict:
    """Разобрать классификации и признаки в записях ClinVar."""
    from .evidence_tools import inspect_clinvar
    return inspect_clinvar(report, dossier)


@mcp.tool()
def search_faers_tool(drug: DrugName) -> dict:
    """Найти сообщения FAERS по препарату."""
    from data_sources import FaersClient
    return FaersClient().search_drug(drug)


@mcp.tool()
def search_clinvar_tool(gene: GeneSymbol, drug: DrugName, variant: OptionalText = "") -> dict:
    """Найти записи ClinVar по гену, препарату и необязательному варианту."""
    from data_sources import ClinVarClient
    return ClinVarClient().search_gene(gene, drug=drug, variant=variant or None)


@mcp.tool()
def search_cpic_guidelines_tool(drug: DrugName, gene: GeneSymbol) -> dict:
    """Найти документы CPIC по препарату и гену."""
    from .research_sources import search_cpic_guidelines
    return search_cpic_guidelines(drug, gene)


@mcp.tool()
def search_clinpgx_annotations_tool(drug: DrugName, gene: GeneSymbol, variant: OptionalText = "") -> dict:
    """Найти аннотации ClinPGx по паре препарат — ген."""
    from .research_sources import search_clinpgx_annotations
    return search_clinpgx_annotations(drug, gene, variant)


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
def search_pharmacogenetic_literature_tool(
    drug: DrugName,
    gene: GeneSymbol,
    variant: OptionalText = "",
    max_results: int = 5,
) -> dict:
    """Найти публикации PubMed для продолжения проверки гипотезы."""
    return search_pharmacogenetic_literature(drug, gene, variant, max_results)


@mcp.tool()
def formulate_hypotheses_tool(
    drug: DrugName,
    gene: GeneSymbol,
    variant: OptionalText = "",
    faers_reports: ReportCount = 0,
    faers_serious_rate: Rate = 0,
    clinvar_records: ReportCount = 0,
    clinvar_pathogenic_records: ReportCount = 0,
    literature_count: ReportCount = 0,
    top_reaction: OptionalText = "",
    literature_titles: OptionalText = "",
) -> dict:
    """Сформировать проверяемые гипотезы по собранному срезу."""
    return formulate_hypotheses(drug, gene, variant, faers_reports, faers_serious_rate, clinvar_records, clinvar_pathogenic_records, literature_count, top_reaction, literature_titles)


@mcp.tool()
def list_pharmacogenetic_tools_tool() -> list[dict]:
    """Показать каталог аналитических инструментов PharmacoGen."""
    return list_pharmacogenetic_tools()


from .clinical_tools import register_clinical_tools
register_clinical_tools(mcp, extended=True)


def main() -> None:
    port = int(os.environ.get("PHARMACOGEN_MCP_PORT", "8000"))
    host = os.environ.get("PHARMACOGEN_MCP_HOST", "127.0.0.1")
    import uvicorn
    from contextlib import asynccontextmanager
    from starlette.applications import Starlette
    http_app = mcp.streamable_http_app(streamable_http_path='/mcp', host=host)
    sse_app = mcp.sse_app(sse_path='/sse', message_path='/messages/', host=host)
    @asynccontextmanager
    async def lifespan(app):
        async with http_app.router.lifespan_context(http_app):
            yield
    app = Starlette(routes=[*sse_app.routes, *http_app.routes], lifespan=lifespan)
    uvicorn.run(app, host=host, port=port, log_level='warning')


if __name__ == "__main__":
    main()
