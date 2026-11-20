"""Useful pharmacogenetic analysis tools exposed through MCP.

The tools consume the evidence already collected by PharmacoGen. They do not
pretend to make a medical decision: their job is to structure signals, expose
gaps and prioritize the next verification step.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field


ToolResult = dict[str, Any]
DrugName = Annotated[str, Field(min_length=2, max_length=120, description="Название препарата")]
GeneSymbol = Annotated[str, Field(min_length=2, max_length=40, description="Символ гена, например CYP2C9")]
OptionalText = Annotated[str, Field(max_length=240, description="Необязательное значение")]
ReportCount = Annotated[int, Field(ge=0, le=1_000_000, description="Количество записей")]
Rate = Annotated[float, Field(ge=0, le=1, description="Доля от 0 до 1")]


def _clean(value: str, name: str, *, required: bool = True) -> str:
    text = " ".join(str(value or "").strip().split())
    if required and not text:
        raise ValueError(f"{name}: заполните это поле")
    return text


def _result(summary: str, details: dict[str, Any], next_steps: list[str]) -> ToolResult:
    return {
        "summary": summary,
        "details": details,
        "next_steps": next_steps,
        "next_step": next_steps[0] if next_steps else "",
        "disclaimer": "Анализ помогает организовать проверку данных и не является клиническим выводом или рекомендацией.",
    }


def synthesize_evidence(
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
) -> ToolResult:
    """Сопоставить уже собранные сводки FAERS и ClinVar."""
    normalized_drug = _clean(drug, "drug")
    normalized_gene = _clean(gene, "gene").upper()
    normalized_variant = _clean(variant, "variant", required=False)
    available_sources = int(faers_available) + int(clinvar_available)
    if faers_available and clinvar_available and faers_reports and clinvar_pathogenic_records:
        summary = "Есть сигналы в двух источниках: требуется предметная проверка связи."
        priority = "высокий"
    elif available_sources >= 1 and (faers_reports or clinvar_records):
        summary = "Есть отдельные сигналы: нужно проверить их согласованность."
        priority = "средний"
    elif available_sources == 2:
        summary = "Источники доступны, но в текущем срезе сильных сигналов не найдено."
        priority = "низкий"
    else:
        summary = "Срез неполный: сначала нужно восстановить недоступный источник."
        priority = "средний"
    missing = []
    if not faers_available:
        missing.append("FAERS недоступен")
    if not clinvar_available:
        missing.append("ClinVar недоступен")
    next_steps = []
    if clinvar_pathogenic_records:
        next_steps.append("Открыть записи ClinVar и проверить классификацию конкретного варианта.")
    if faers_reports:
        next_steps.append("Проверить профиль реакций FAERS и не трактовать число сообщений как частоту.")
    if normalized_variant:
        next_steps.append(f"Сопоставить вариант {normalized_variant} с публикациями по {normalized_drug} и {normalized_gene}.")
    else:
        next_steps.append("Уточнить вариант или генотип перед предметной интерпретацией.")
    if missing:
        next_steps.insert(0, "; ".join(missing) + ".")
    return _result(
        summary,
        {
            "pair": f"{normalized_drug} × {normalized_gene}",
            "variant": normalized_variant or "не указан",
            "priority": priority,
            "available_sources": available_sources,
            "faers": {"available": faers_available, "reports": faers_reports, "serious_rate": round(faers_serious_rate, 3), "top_reaction": _clean(top_reaction, "top_reaction", required=False) or "нет данных"},
            "clinvar": {"available": clinvar_available, "records": clinvar_records, "pathogenic_records": clinvar_pathogenic_records},
        },
        next_steps[:4],
    )


def prioritize_variant_review(
    drug: DrugName,
    gene: GeneSymbol,
    variant: OptionalText = "",
    classification: OptionalText = "",
    review_status: OptionalText = "",
    traits: OptionalText = "",
) -> ToolResult:
    """Выбрать приоритет проверки варианта по записи ClinVar."""
    normalized_drug = _clean(drug, "drug")
    normalized_gene = _clean(gene, "gene").upper()
    normalized_variant = _clean(variant, "variant", required=False)
    normalized_classification = _clean(classification, "classification", required=False)
    classification_lower = normalized_classification.casefold()
    if "pathogenic" in classification_lower:
        priority, status = "высокий", "классификация требует первоочередной проверки"
    elif normalized_variant:
        priority, status = "средний", "вариант найден, но классификация требует уточнения"
    else:
        priority, status = "низкий", "вариант для приоритизации не указан"
    next_steps = [
        f"Проверить запись ClinVar для {normalized_gene} и варианта {normalized_variant or 'не указан'}.",
        f"Найти публикации о взаимодействии {normalized_drug} × {normalized_gene}.",
    ]
    if normalized_classification:
        next_steps.insert(0, f"Сверить классификацию «{normalized_classification}» с критериями и датой оценки.")
    return _result(
        status,
        {
            "pair": f"{normalized_drug} × {normalized_gene}",
            "variant": normalized_variant or "не указан",
            "priority": priority,
            "classification": normalized_classification or "не указана",
            "review_status": _clean(review_status, "review_status", required=False) or "не указан",
            "traits": _clean(traits, "traits", required=False) or "не указаны",
        },
        next_steps,
    )


def audit_evidence_quality(
    faers_available: bool = False,
    faers_reports: ReportCount = 0,
    clinvar_available: bool = False,
    clinvar_records: ReportCount = 0,
    has_variant: bool = False,
    has_source_links: bool = False,
) -> ToolResult:
    """Проверить полноту среза перед его использованием в выводе."""
    checks = {
        "FAERS отвечает": faers_available,
        "ClinVar отвечает": clinvar_available,
        "FAERS содержит записи": faers_reports > 0,
        "ClinVar содержит записи": clinvar_records > 0,
        "вариант указан": has_variant,
        "ссылки на источники сохранены": has_source_links,
    }
    passed = sum(checks.values())
    score = round(passed / len(checks) * 100)
    missing = [name for name, ok in checks.items() if not ok]
    if score >= 85:
        summary = "Срез достаточно полный для исследовательского просмотра."
    elif score >= 55:
        summary = "Срез частично готов: перед выводом нужно закрыть пробелы."
    else:
        summary = "Срез недостаточен для содержательного сопоставления."
    return _result(
        summary,
        {"quality_score": score, "passed_checks": passed, "total_checks": len(checks), "checks": checks, "missing": missing},
        [f"Закрыть: {', '.join(missing)}."] if missing else ["Сохранить ссылки и перейти к ручной проверке исходных записей."],
    )


def list_pharmacogenetic_tools() -> list[dict[str, Any]]:
    """Вернуть каталог инструментов, которые анализируют текущий отчёт."""
    return [
        {
            "name": "synthesize_evidence",
            "title": "Синтез доказательств",
            "category": "анализ текущего отчёта",
            "required": ["drug", "gene"],
            "parameters": {
                "drug": {"type": "string", "description": "Препарат из текущего исследования"},
                "gene": {"type": "string", "description": "Ген из текущего исследования"},
                "variant": {"type": "string", "description": "Необязательно: вариант или генотип"},
                "faers_available": {"type": "boolean", "default": False, "description": "FAERS ответил"},
                "faers_reports": {"type": "integer", "minimum": 0, "maximum": 1000000, "default": 0, "unit": "сообщений"},
                "faers_serious_rate": {"type": "number", "minimum": 0, "maximum": 1, "default": 0, "unit": "доля"},
                "clinvar_available": {"type": "boolean", "default": False, "description": "ClinVar ответил"},
                "clinvar_records": {"type": "integer", "minimum": 0, "maximum": 1000000, "default": 0, "unit": "записей"},
                "clinvar_pathogenic_records": {"type": "integer", "minimum": 0, "maximum": 1000000, "default": 0, "unit": "записей"},
                "top_reaction": {"type": "string", "description": "Самая частая реакция, если есть"},
            },
            "source": "локальная аналитика PharmacoGen",
        },
        {
            "name": "prioritize_variant_review",
            "title": "Приоритет проверки варианта",
            "category": "ClinVar",
            "required": ["drug", "gene"],
            "parameters": {
                "drug": {"type": "string", "description": "Препарат"},
                "gene": {"type": "string", "description": "Символ гена"},
                "variant": {"type": "string", "description": "Вариант из записи ClinVar"},
                "classification": {"type": "string", "description": "Классификация ClinVar"},
                "review_status": {"type": "string", "description": "Статус проверки ClinVar"},
                "traits": {"type": "string", "description": "Связанные признаки"},
            },
            "source": "локальная аналитика PharmacoGen",
        },
        {
            "name": "audit_evidence_quality",
            "title": "Контроль качества данных",
            "category": "проверка полноты",
            "required": [],
            "parameters": {
                "faers_available": {"type": "boolean", "default": False, "description": "FAERS ответил"},
                "faers_reports": {"type": "integer", "minimum": 0, "maximum": 1000000, "default": 0, "unit": "сообщений"},
                "clinvar_available": {"type": "boolean", "default": False, "description": "ClinVar ответил"},
                "clinvar_records": {"type": "integer", "minimum": 0, "maximum": 1000000, "default": 0, "unit": "записей"},
                "has_variant": {"type": "boolean", "default": False, "description": "Вариант указан"},
                "has_source_links": {"type": "boolean", "default": False, "description": "Ссылки сохранены"},
            },
            "source": "локальная аналитика PharmacoGen",
        },
    ]
