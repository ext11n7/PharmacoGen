from agents import SynthesisAgent, normalize_term, run_investigation


class FakeFaers:
    source_url = "https://example.test/faers"

    def search_drug(self, drug):
        return {"status": "ok", "source": self.source_url, "total_reports": 10, "preview_reports": 10, "serious_preview": 4, "serious_rate": 0.4, "top_reactions": []}


class FakeClinVar:
    source_url = "https://example.test/clinvar"

    def search_gene(self, gene, drug=None):
        return {"status": "ok", "source": self.source_url, "total_records": 8, "returned_records": 2, "pathogenic_records": 1, "records": []}


class FakeClinVarWithVariant(FakeClinVar):
    def search_gene(self, gene, drug=None, variant=None):
        return super().search_gene(gene, drug=drug) | {"query_variant": variant}


def test_normalize_term_handles_aliases():
    assert normalize_term("Кумадин") == "warfarin"
    assert normalize_term(" cyp2c9 ") == "cyp2c9"


def test_investigation_has_all_agent_outputs():
    report = run_investigation("Coumadin", "cyp2c9", {"faers": FakeFaers(), "clinvar": FakeClinVar()})
    assert report.normalized_query == {"drug": "warfarin", "gene": "CYP2C9"}
    assert report.synthesis["confidence"] == "weak"
    assert "отдельной проверки" in report.synthesis["headline"]
    assert {event.agent for event in report.events} == {"Entity Agent", "FAERS Agent", "ClinVar Agent", "Synthesis Agent"}


def test_synthesis_does_not_overclaim():
    result = SynthesisAgent().run("warfarin", "CYP2C9", {"status": "ok", "total_reports": 0, "serious_rate": 0}, {"status": "ok", "pathogenic_records": 0}, [])
    assert result["confidence"] == "weak"
    assert result["not_medical_advice"] is True


def test_variant_is_normalized_and_reported_as_preliminary():
    report = run_investigation(
        "warfarin",
        "CYP2C9",
        {"faers": FakeFaers(), "clinvar": FakeClinVarWithVariant()},
        variant=" *2 / *3 ",
    )
    assert report.normalized_query["variant"] == "*2/*3"
    assert report.clinvar["query_variant"] == "*2/*3"
    assert report.synthesis["variant"]["status"] == "review"
    assert report.synthesis["variant"]["confidence"] == "exploratory"

