import json

from mcp_servers import research_sources, research_summary


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_cpic_matches_gene_and_preserves_metadata(monkeypatch):
    monkeypatch.setattr(research_sources.requests, "get", lambda *args, **kwargs: FakeResponse([
        {"id": 1, "name": "CYP2C9 and warfarin", "genes": ["CYP2C9"], "url": "https://example.org/1"},
        {"id": 2, "name": "Other", "genes": ["OTHER"], "url": "https://example.org/2"},
    ]))
    result = research_sources.search_cpic_guidelines("warfarin", "cyp2c9")
    assert result["status"] == "ok"
    assert [item["id"] for item in result["records"]] == [1]


def test_abstracts_match_by_pmid_and_keep_pubmed_order(monkeypatch):
    monkeypatch.setattr(research_sources.requests, "get", lambda *args, **kwargs: FakeResponse({"resultList": {"result": [
        {"pmid": "2", "abstractText": "<b>Results</b> second", "pubTypeList": {"pubType": ["Review"]}},
        {"pmid": "1", "abstractText": "First", "isOpenAccess": "Y", "pmcid": "PMC1"},
    ]}}))
    result = research_sources.enrich_pubmed_records([{"pmid": "1"}, {"pmid": "2"}])
    assert [item["abstract"] for item in result] == ["First", "Results second"]
    assert result[0]["open_access"] and result[1]["publication_types"] == ["Review"]


def test_model_output_rejects_fabricated_reference(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("PHARMACOGEN_LLM_MODEL", "test-model")
    output = {"sections": [{"title": "Обзор", "paragraphs": [{"text": "Утверждение", "source_ids": ["PMID:999"]}]}]}
    monkeypatch.setattr(research_summary.requests, "post", lambda *args, **kwargs: FakeResponse({"choices": [{"message": {"content": json.dumps(output)}}]}))
    report = {"query": {"drug": "warfarin", "gene": "CYP2C9"}}
    dossier = {"literature": {"details": {"records": [{"pmid": "1", "abstract": "Abstract"}]}}}
    assert research_summary.create_summary(report, dossier)["status"] == "unavailable"


def test_model_returns_valid_cited_review(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("PHARMACOGEN_LLM_MODEL", "test-model")
    output = {"sections": [{"title": "Обзор", "paragraphs": [{"text": "Авторы исследовали связь.", "source_ids": ["PMID:1"]}]}]}
    monkeypatch.setattr(research_summary.requests, "post", lambda *args, **kwargs: FakeResponse({"choices": [{"message": {"content": json.dumps(output)}}]}))
    report = {"query": {"drug": "warfarin", "gene": "CYP2C9"}}
    dossier = {"literature": {"details": {"records": [{"pmid": "1", "abstract": "Abstract"}]}}}
    assert research_summary.create_summary(report, dossier)["status"] == "ok"


def test_clinpgx_keeps_pair_context_and_filters_unrelated_records(monkeypatch):
    monkeypatch.setattr(research_sources.requests, "get", lambda *args, **kwargs: FakeResponse({"status": "success", "data": [
        {"accessionId": "PA123", "name": "CYP2C9 and warfarin", "relatedChemicals": [{"name": "warfarin"}], "location": {"genes": [{"symbol": "CYP2C9"}], "displayName": "CYP2C9*2"}, "allelePhenotypes": [{"allele": "*2", "phenotype": "Source text"}]},
        {"accessionId": "PA456", "relatedChemicals": [{"name": "other"}], "location": {"genes": [{"symbol": "CYP2C9"}]}},
    ]}))
    result = research_sources.search_clinpgx_annotations("warfarin", "CYP2C9", "rs1799853")
    assert result["total"] == 1
    assert result["records"][0]["scope"] == "drug_gene_pair"
    assert result["records"][0]["statements"][0]["text"] == "Source text"
