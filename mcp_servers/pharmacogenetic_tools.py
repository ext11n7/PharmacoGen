"""Deterministic pharmacogenetics helpers exposed through MCP.

These tools prepare and compare evidence queries. They do not make a clinical
classification and deliberately keep external evidence retrieval in separate
FAERS, ClinVar, FDA and PubMed connectors.
"""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import Field


ToolResult = dict[str, Any]
DrugName = Annotated[str, Field(min_length=2, max_length=120, description="Название препарата")]
GeneSymbol = Annotated[str, Field(min_length=2, max_length=40, description="Символ гена, например CYP2C9")]
VariantName = Annotated[str, Field(max_length=120, description="Вариант или аллель, например rs1799853 или *2")]
MaxResults = Annotated[int, Field(ge=1, le=20, description="Максимум результатов для внешнего поиска")]
EvidenceCount = Annotated[int, Field(ge=0, le=1_000_000, description="Количество найденных записей")]


def _clean(value: str, name: str, *, required: bool = True) -> str:
    text = " ".join(str(value or "").strip().split())
    if required and not text:
        raise ValueError(f"{name}: значение не должно быть пустым")
    return text


def _result(summary: str, details: dict[str, Any], next_step: str) -> ToolResult:
    return {
        "summary": summary,
        "details": details,
        "next_step": next_step,
        "disclaimer": "Результат помогает организовать поиск и не является клиническим выводом или рекомендацией.",
    }


def normalize_pharmacogenetic_query(drug: DrugName, gene: GeneSymbol, variant: VariantName = "") -> ToolResult:
    """Нормализовать три сущности для согласованного поиска по источникам."""
    normalized_drug = _clean(drug, "drug")
    normalized_gene = _clean(gene, "gene").upper()
    normalized_variant = _clean(variant, "variant", required=False).upper()
    pair = f"{normalized_drug} {normalized_gene}"
    return _result(
        "Сущности подготовлены для межисточникового поиска.",
        {
            "drug": normalized_drug,
            "gene": normalized_gene,
            "variant": normalized_variant or None,
            "faers_query": pair,
            "clinvar_query": f"{normalized_gene} {normalized_variant}".strip(),
            "pubmed_query": f'"{normalized_drug}" AND "{normalized_gene}"',
        },
        "Передать запросы агентам FAERS, ClinVar и внешнему поиску литературы.",
    )


def build_evidence_query(
    drug: DrugName,
    gene: GeneSymbol,
    variant: VariantName = "",
    max_results: MaxResults = 5,
) -> ToolResult:
    """Собрать отдельные поисковые задания для источников проекта."""
    normalized = normalize_pharmacogenetic_query(drug, gene, variant)
    data = normalized["details"]
    return _result(
        "План сбора доказательств собран.",
        {
            "entities": {"drug": data["drug"], "gene": data["gene"], "variant": data["variant"]},
            "requests": [
                {"source": "FAERS", "purpose": "частота спонтанных сообщений", "query": data["faers_query"]},
                {"source": "ClinVar", "purpose": "вариант и клиническая интерпретация", "query": data["clinvar_query"]},
                {"source": "PubMed", "purpose": "публикации о связи препарата и гена", "query": data["pubmed_query"], "max_results": max_results},
                {"source": "FDA", "purpose": "маркировка и сведения о препарате", "query": data["drug"]},
            ],
        },
        "Запустить поиск, затем сопоставить результаты по варианту и источнику.",
    )


def classify_variant_for_review(gene: GeneSymbol, variant: VariantName) -> ToolResult:
    """Определить формат записи варианта и следующий источник проверки."""
    normalized_gene = _clean(gene, "gene").upper()
    normalized_variant = _clean(variant, "variant").upper()
    if re.fullmatch(r"RS\d+", normalized_variant):
        notation = "идентификатор dbSNP"
    elif "*" in normalized_variant:
        notation = "звёздный аллель"
    elif re.search(r"\b[CGP]?\.\d+", normalized_variant):
        notation = "HGVS-подобная запись"
    else:
        notation = "свободная запись"
    return _result(
        "Вариант подготовлен к проверке, клиническая классификация не выполнялась.",
        {
            "gene": normalized_gene,
            "variant": normalized_variant,
            "notation": notation,
            "review_status": "готов к поиску",
            "recommended_source": "ClinVar",
        },
        "Проверить вариант в ClinVar и сопоставить его с литературой и препаратом.",
    )


def compare_source_signals(
    faers_reports: EvidenceCount = 0,
    clinvar_records: EvidenceCount = 0,
    pathogenic_records: EvidenceCount = 0,
    literature_hits: EvidenceCount = 0,
) -> ToolResult:
    """Сопоставить уже собранные количества записей без вывода о причинности."""
    counts = {
        "FAERS сообщений": faers_reports,
        "ClinVar записей": clinvar_records,
        "ClinVar записей с клиническим сигналом": pathogenic_records,
        "публикаций": literature_hits,
    }
    active = sum(value > 0 for value in counts.values())
    if faers_reports and clinvar_records and pathogenic_records:
        state = "есть сигналы в нескольких источниках"
    elif active >= 2:
        state = "есть отдельные сигналы для проверки"
    elif active == 1:
        state = "сигнал найден только в одном источнике"
    else:
        state = "данных для сравнения пока недостаточно"
    return _result(
        state,
        {"counts": counts, "active_sources": active, "comparison_state": state},
        "Открыть исходные записи и проверить согласованность варианта, препарата и контекста.",
    )


def list_pharmacogenetic_tools() -> list[dict[str, Any]]:
    """Вернуть каталог локальных инструментов и их динамические формы."""
    return [
        {
            "name": "normalize_pharmacogenetic_query",
            "title": "Нормализация запроса",
            "category": "подготовка поиска",
            "parameters": {
                "drug": {"type": "string", "description": "Например warfarin"},
                "gene": {"type": "string", "description": "Например CYP2C9"},
                "variant": {"type": "string", "description": "Необязательно: rs1799853 или *2"},
            },
            "source": "локальная логика PharmacoGen",
        },
        {
            "name": "build_evidence_query",
            "title": "План сбора доказательств",
            "category": "маршрутизация источников",
            "parameters": {
                "drug": {"type": "string", "description": "Название препарата"},
                "gene": {"type": "string", "description": "Символ гена"},
                "variant": {"type": "string", "description": "Необязательно: вариант или аллель"},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5, "unit": "записей"},
            },
            "source": "локальная логика PharmacoGen",
        },
        {
            "name": "classify_variant_for_review",
            "title": "Подготовка варианта",
            "category": "ClinVar",
            "parameters": {
                "gene": {"type": "string", "description": "Символ гена"},
                "variant": {"type": "string", "description": "Например rs1799853, *2 или c.430C>T"},
            },
            "source": "локальная логика PharmacoGen",
        },
        {
            "name": "compare_source_signals",
            "title": "Сопоставление сигналов",
            "category": "синтез доказательств",
            "parameters": {
                "faers_reports": {"type": "integer", "minimum": 0, "maximum": 1000000, "default": 0, "unit": "сообщений"},
                "clinvar_records": {"type": "integer", "minimum": 0, "maximum": 1000000, "default": 0, "unit": "записей"},
                "pathogenic_records": {"type": "integer", "minimum": 0, "maximum": 1000000, "default": 0, "unit": "записей"},
                "literature_hits": {"type": "integer", "minimum": 0, "maximum": 1000000, "default": 0, "unit": "публикаций"},
            },
            "source": "локальная логика PharmacoGen",
        },
    ]
