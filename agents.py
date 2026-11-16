"""Multi-agent evidence collection for the PharmacoGen prototype."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import re

from data_sources import ClinVarClient, FaersClient, SourceError


@dataclass
class AgentEvent:
    agent: str
    status: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class EvidenceReport:
    query: dict[str, str]
    normalized_query: dict[str, str]
    faers: dict[str, Any]
    clinvar: dict[str, Any]
    synthesis: dict[str, Any]
    events: list[AgentEvent]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["events"] = [asdict(event) for event in self.events]
        return result


ALIAS_MAP = {
    "coumadin": "warfarin",
    "варфарин": "warfarin",
    "кумадин": "warfarin",
    "карбамазепин": "carbamazepine",
    "тегретол": "carbamazepine",
    "клопидогрел": "clopidogrel",
    "плавикс": "clopidogrel",
}


def normalize_term(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    return ALIAS_MAP.get(value.casefold(), value)


def normalize_variant(value: str) -> str:
    return re.sub(r"\s+", "", value.strip())


def interpret_variant(gene: str, variant: str) -> dict[str, str]:
    if not variant:
        return {
            "status": "not_provided",
            "label": "Вариант не указан",
            "phenotype": "Фенотип не определён",
            "basis": "Добавьте rs-идентификатор или генотип для предварительного сопоставления.",
            "confidence": "not_assessed",
        }

    token = variant.casefold()
    known_pairs = {
        "cyp2c9": ("*2", "*3"),
        "cyp2c19": ("*2", "*3"),
        "hla-b": ("*57:01", "*15:02"),
    }
    matched = known_pairs.get(gene.casefold(), ())
    if matched and any(item.casefold() in token for item in matched):
        return {
            "status": "review",
            "label": "Есть вариант для отдельной проверки",
            "phenotype": "Возможна изменённая функция",
            "basis": "Сработало предварительное сопоставление по гену и обозначению аллеля; клиническая интерпретация не выполняется автоматически.",
            "confidence": "exploratory",
        }
    return {
        "status": "review",
        "label": "Вариант найден в запросе",
        "phenotype": "Фенотип требует проверки",
        "basis": "Вариант передан в поиск источников; для вывода нужна подтверждённая классификация и контекст генотипа.",
        "confidence": "exploratory",
    }


class EntityAgent:
    name = "Entity Agent"

    def run(self, drug: str, gene: str, variant: str, events: list[AgentEvent]) -> dict[str, str]:
        normalized = {"drug": normalize_term(drug), "gene": gene.strip().upper()}
        if variant:
            normalized["variant"] = normalize_variant(variant)
        detail = f"{normalized['drug']} + {normalized['gene']}"
        if normalized.get("variant"):
            detail += f" + {normalized['variant']}"
        events.append(AgentEvent(self.name, "done", f"Нормализованы сущности: {detail}"))
        return normalized


class FaersAgent:
    name = "FAERS Agent"

    def __init__(self, client: FaersClient | None = None):
        self.client = client or FaersClient()

    def run(self, drug: str, events: list[AgentEvent]) -> dict[str, Any]:
        events.append(AgentEvent(self.name, "running", f"Запрос openFDA FAERS для {drug}"))
        try:
            result = self.client.search_drug(drug)
        except SourceError as exc:
            events.append(AgentEvent(self.name, "error", str(exc)))
            return {"status": "error", "error": str(exc), "source": self.client.source_url}
        events.append(AgentEvent(self.name, "done", f"Найдено сообщений: {result['total_reports']:,}"))
        return result


class ClinVarAgent:
    name = "ClinVar Agent"

    def __init__(self, client: ClinVarClient | None = None):
        self.client = client or ClinVarClient()

    def run(self, gene: str, drug: str, variant: str, events: list[AgentEvent]) -> dict[str, Any]:
        detail = f"{gene} + {drug}" + (f" + {variant}" if variant else "")
        events.append(AgentEvent(self.name, "running", f"Поиск ClinVar для пары {detail}"))
        try:
            if variant:
                result = self.client.search_gene(gene, drug=drug, variant=variant)
            else:
                result = self.client.search_gene(gene, drug=drug)
        except SourceError as exc:
            events.append(AgentEvent(self.name, "error", str(exc)))
            return {"status": "error", "error": str(exc), "source": self.client.source_url}
        events.append(AgentEvent(self.name, "done", f"Получено записей ClinVar: {result['total_records']:,}"))
        return result


class SynthesisAgent:
    name = "Synthesis Agent"

    def run(self, drug: str, gene: str, faers: dict[str, Any], clinvar: dict[str, Any], events: list[AgentEvent], variant: str = "") -> dict[str, Any]:
        events.append(AgentEvent(self.name, "running", "Сопоставление доказательств и проверка ограничений"))
        faers_ok = faers.get("status") == "ok"
        clinvar_ok = clinvar.get("status") == "ok"
        serious_rate = faers.get("serious_rate") if faers_ok else None
        pathogenic = clinvar.get("pathogenic_records", 0) if clinvar_ok else 0

        if faers_ok and clinvar_ok and faers.get("total_reports", 0) and pathogenic:
            confidence = "exploratory"
            headline = f"Есть основание проверить связь {drug} + {gene}; это гипотеза, а не доказанный эффект."
        elif faers_ok and clinvar_ok:
            confidence = "weak"
            headline = "Данные собраны, но автоматического основания для сильной гипотезы недостаточно."
        else:
            confidence = "incomplete"
            headline = "Отчёт неполный: один или оба источника недоступны."

        limitations = [
            "FAERS основан на спонтанных сообщениях: число сообщений не равно частоте и не доказывает причинность.",
            "ClinVar описывает клиническую интерпретацию вариантов, но сам по себе не доказывает фармакогенетический эффект.",
            "В этой версии нет индивидуальных данных пациента, дозировки, временной последовательности или поправки на сопутствующие препараты.",
        ]
        result = {
            "headline": headline,
            "confidence": confidence,
            "variant": interpret_variant(gene, variant),
            "why": [
                f"FAERS: {faers.get('total_reports', 0):,} сообщений по препарату {drug}." if faers_ok else "FAERS: данные недоступны.",
                f"ClinVar: {pathogenic:,} записей с классификацией pathogenic/likely pathogenic для {gene}." if clinvar_ok else "ClinVar: данные недоступны.",
                f"Доля серьёзных сообщений в превью FAERS: {serious_rate:.1%}." if serious_rate is not None else "Доля серьёзных сообщений: не рассчитана.",
            ],
            "limitations": limitations,
            "not_medical_advice": True,
        }
        events.append(AgentEvent(self.name, "done", f"Итоговая сила сигнала: {confidence}"))
        return result


def run_investigation(drug: str, gene: str, clients: dict[str, Any] | None = None, variant: str = "") -> EvidenceReport:
    events: list[AgentEvent] = []
    normalized = EntityAgent().run(drug, gene, variant, events)
    clients = clients or {}
    faers = FaersAgent(clients.get("faers")).run(normalized["drug"], events)
    clinvar = ClinVarAgent(clients.get("clinvar")).run(normalized["gene"], normalized["drug"], normalized.get("variant", ""), events)
    synthesis = SynthesisAgent().run(normalized["drug"], normalized["gene"], faers, clinvar, events, variant=normalized.get("variant", ""))
    query = {"drug": drug, "gene": gene}
    if variant:
        query["variant"] = variant
    return EvidenceReport(
        query=query,
        normalized_query=normalized,
        faers=faers,
        clinvar=clinvar,
        synthesis=synthesis,
        events=events,
    )

