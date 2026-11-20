import pytest

from web_server import _validate_mcp_arguments


def test_mcp_request_validation_explains_empty_required_fields():
    with pytest.raises(ValueError, match="Препарат, Ген"):
        _validate_mcp_arguments("stdio", "synthesize_evidence_tool", {})


def test_mcp_request_validation_accepts_report_summary():
    _validate_mcp_arguments(
        "stdio",
        "synthesize_evidence_tool",
        {"drug": "warfarin", "gene": "CYP2C9", "faers_reports": 10, "faers_serious_rate": 0.2},
    )
