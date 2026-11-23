"""Small, testable clients for the two approved public sources."""

from __future__ import annotations

from collections import Counter
from typing import Any
import requests


class SourceError(RuntimeError):
    pass


class HttpClient:
    def __init__(self, timeout: int = 20, session: requests.Session | None = None):
        self.timeout = timeout
        self.session = session or requests.Session()

    def get_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise SourceError(f"Ошибка запроса к источнику: {exc}") from exc
        except ValueError as exc:
            raise SourceError("Источник вернул некорректный JSON") from exc


class FaersClient(HttpClient):
    base_url = "https://api.fda.gov/drug/event.json"
    source_url = "https://open.fda.gov/apis/drug/event/"

    def search_drug(self, drug: str) -> dict[str, Any]:
        search = f'patient.drug.openfda.generic_name:"{drug}"'
        try:
            summary = self.get_json(self.base_url, {"search": search, "limit": 1})
        except SourceError as exc:
            if isinstance(exc.__cause__, requests.HTTPError) and exc.__cause__.response is not None and exc.__cause__.response.status_code == 404:
                return {"status": "ok", "source": self.source_url, "query": search, "total_reports": 0, "preview_reports": 0, "serious_preview": 0, "serious_rate": 0, "top_reactions": [], "sample_report_id": None}
            raise
        total = int(summary.get("meta", {}).get("results", {}).get("total", 0))
        serious = 0
        reactions: Counter[str] = Counter()
        sample = summary.get("results", [{}])[0] if summary.get("results") else {}
        preview = self.get_json(self.base_url, {"search": search, "limit": 20})
        for report in preview.get("results", []):
            if str(report.get("serious", "0")) == "1":
                serious += 1
            for reaction in report.get("patient", {}).get("reaction", []):
                term = reaction.get("reactionmeddrapt")
                if term:
                    reactions[term] += 1
        preview_count = len(preview.get("results", []))
        serious_rate = serious / preview_count if preview_count else 0.0
        return {
            "status": "ok",
            "source": self.source_url,
            "query": search,
            "total_reports": total,
            "preview_reports": preview_count,
            "serious_preview": serious,
            "serious_rate": serious_rate,
            "top_reactions": [{"term": term, "count": count} for term, count in reactions.most_common(8)],
            "sample_report_id": sample.get("safetyreportid"),
            "disclaimer": summary.get("meta", {}).get("disclaimer"),
        }


class ClinVarClient(HttpClient):
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    source_url = "https://www.ncbi.nlm.nih.gov/clinvar/"

    def search_gene(self, gene: str, drug: str | None = None, variant: str | None = None, retmax: int = 10) -> dict[str, Any]:
        term = f"{gene}[gene name]"
        if drug:
            term += f" AND {drug}[All Fields]"
        if variant:
            term += f" AND {variant}[All Fields]"
        search = self.get_json(self.search_url, {
            "db": "clinvar", "term": term, "retmode": "json", "retmax": retmax,
        })
        result = search.get("esearchresult", {})
        ids = result.get("idlist", [])
        records: list[dict[str, Any]] = []
        if ids:
            summary = self.get_json(self.summary_url, {
                "db": "clinvar", "id": ",".join(ids), "retmode": "json",
            })
            for uid in summary.get("result", {}).get("uids", []):
                record = summary["result"].get(uid, {})
                classification = record.get("germline_classification", {})
                description = classification.get("description", "Unknown")
                records.append({
                    "uid": uid,
                    "accession": record.get("accession", ""),
                    "title": record.get("title", ""),
                    "classification": description,
                    "review_status": classification.get("review_status", ""),
                    "last_evaluated": classification.get("last_evaluated", ""),
                    "traits": [item.get("trait_name", "") for item in classification.get("trait_set", [])],
                    "url": f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{uid}/",
                })
        pathogenic_records = sum("pathogenic" in item["classification"].casefold() for item in records)
        return {
            "status": "ok",
            "source": self.source_url,
            "query": term,
            "total_records": int(result.get("count", 0)),
            "returned_records": len(records),
            "pathogenic_records": pathogenic_records,
            "records": records,
        }

