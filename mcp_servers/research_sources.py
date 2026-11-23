"""Additional public evidence, kept separate from clinical interpretation."""

from __future__ import annotations

import html
import re
from typing import Any

import requests


def enrich_pubmed_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach Europe PMC metadata by PMID without changing PubMed ordering."""
    ids = [str(item.get("pmid", "")) for item in records if str(item.get("pmid", "")).isdigit()]
    if not ids:
        return records
    try:
        response = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": f"EXT_ID:({' OR '.join(ids)}) AND SRC:MED", "format": "json", "resultType": "core", "pageSize": len(ids)},
            timeout=8,
        )
        response.raise_for_status()
        matches = {str(item.get("pmid")): item for item in response.json().get("resultList", {}).get("result", [])}
        for record in records:
            item = matches.get(str(record.get("pmid")), {})
            abstract = html.unescape(re.sub(r"<[^>]+>", " ", str(item.get("abstractText") or "")))
            record.update({
                "abstract": re.sub(r"\s+", " ", abstract).strip(),
                "publication_types": item.get("pubTypeList", {}).get("pubType", []),
                "doi": item.get("doi") or "",
                "pmcid": item.get("pmcid") or "",
                "open_access": item.get("isOpenAccess") == "Y",
                "abstract_source": "Europe PMC / PubMed",
            })
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        for record in records:
            record["abstract_unavailable"] = True
    missing = [item for item in records if not item.get('abstract')]
    if missing:
        try:
            import xml.etree.ElementTree as ET
            response = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi', params={'db': 'pubmed', 'id': ','.join(str(x['pmid']) for x in missing), 'retmode': 'xml'}, timeout=10)
            response.raise_for_status()
            # This API response is bounded before XML parsing; external entities are not resolved by ElementTree.
            if len(response.content) > 2_000_000:
                raise ValueError('Response too large')
            root = ET.fromstring(response.content)
            by_id = {row.findtext('MedlineCitation/PMID'): row for row in root.findall('PubmedArticle')}
            for record in missing:
                row = by_id.get(str(record['pmid']))
                if row is None:
                    continue
                record['abstract'] = '\n'.join(''.join(x.itertext()) for x in row.findall('MedlineCitation/Article/Abstract/AbstractText'))
                record['publication_types'] = [''.join(x.itertext()) for x in row.findall('MedlineCitation/Article/PublicationTypeList/PublicationType')]
                record['abstract_source'] = 'PubMed / NCBI efetch'
                record['abstract_unavailable'] = not bool(record['abstract'])
        except (requests.RequestException, ValueError, AttributeError, ET.ParseError):
            pass
    return records


def search_cpic_guidelines(drug: str, gene: str) -> dict[str, Any]:
    """Find CPIC guideline metadata for an exact gene and a drug name."""
    drug, gene = drug.strip(), gene.strip().upper()
    if not drug or not gene or len(drug) > 120 or len(gene) > 40:
        raise ValueError("Укажите препарат и ген")
    try:
        response = requests.get(
            "https://api.cpicpgx.org/v1/guideline",
            params={"select": "id,name,genes,url,version", "name": f"ilike.*{drug}*", "limit": 30}, timeout=8,
        )
        response.raise_for_status()
        records = [item for item in response.json() if gene in [str(g).upper() for g in (item.get("genes") or [])]]
        return {"status": "ok", "source": "CPIC", "query": {"drug": drug, "gene": gene}, "records": records, "total": len(records)}
    except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
        return {"status": "unavailable", "source": "CPIC", "query": {"drug": drug, "gene": gene}, "records": [], "total": 0, "error": str(exc)}


def search_clinpgx_annotations(drug: str, gene: str, variant: str = "") -> dict[str, Any]:
    """Return source annotations as pair-level context, without matching genotypes."""
    drug, gene, variant = drug.strip(), gene.strip().upper(), variant.strip()
    if not drug or not gene or len(drug) > 120 or len(gene) > 40 or len(variant) > 240:
        raise ValueError("Укажите препарат и ген")
    try:
        response = requests.get("https://api.clinpgx.org/v1/data/clinicalAnnotation", params={"relatedChemicals.name": drug, "location.genes.symbol": gene}, timeout=8)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "success" or not isinstance(payload.get("data"), list):
            raise ValueError("ClinPGx вернул неожиданный формат")
        records = []
        for item in payload["data"]:
            if not isinstance(item, dict):
                continue
            chemicals = item.get("relatedChemicals") or []
            genes = (item.get("location") or {}).get("genes") or []
            if not any(str(x.get("name", "")).casefold() == drug.casefold() for x in chemicals if isinstance(x, dict)):
                continue
            if not any(str(x.get("symbol", "")).upper() == gene for x in genes if isinstance(x, dict)):
                continue
            accession = str(item.get("accessionId") or "")
            if not re.fullmatch(r"PA\d+", accession):
                continue
            location = item.get("location") or {}
            records.append({"id": accession, "title": str(item.get("name") or ""), "variant": str(location.get("displayName") or location.get("rsid") or ""), "evidence_level": str((item.get("levelOfEvidence") or {}).get("term") or ""), "url": f"https://www.clinpgx.org/clinicalAnnotation/{accession}", "statements": [{"allele": str(row.get("allele") or ""), "text": str(row.get("phenotype") or "")} for row in (item.get("allelePhenotypes") or [])[:4] if isinstance(row, dict)], "scope": "drug_gene_pair"})
        return {"status": "ok", "source": "ClinPGx", "query": {"drug": drug, "gene": gene, "variant": variant}, "total": len(records), "records": records[:8]}
    except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
        return {"status": "unavailable", "source": "ClinPGx", "query": {"drug": drug, "gene": gene, "variant": variant}, "records": [], "total": 0, "error": str(exc)}
