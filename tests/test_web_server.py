import pytest

import json

from web_server import _validate_mcp_arguments, build_mcp_dossier


def _fake_mcp_call(source, tool, arguments):
    if tool == "synthesize_evidence_tool":
        value = {"summary": "Сигналы сопоставлены", "details": {"priority": "высокий", "available_sources": 2}, "next_steps": ["Проверить ClinVar"]}
    elif tool == "audit_evidence_quality_tool":
        value = {"summary": "Срез готов", "details": {"quality_score": 83}, "next_steps": ["Проверить ссылку"]}
    elif tool == "formulate_hypotheses_tool":
        value = {"summary": "Сформировано гипотез: 1", "details": {"hypotheses": [{"statement": "Проверить связь", "next_step": "Открыть публикации"}]}, "next_steps": ["Открыть публикации"]}
    else:
        value = {"summary": "Вариант требует проверки", "details": {"variant": "rs1799853", "priority": "средний"}, "next_steps": ["Открыть запись"]}
    return {"result": {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}]}, "trace": [{"method": "tools/call"}]}


def test_mcp_request_validation_explains_empty_required_fields():
    with pytest.raises(ValueError, match="Препарат, Ген"):
        _validate_mcp_arguments("stdio", "synthesize_evidence_tool", {})


def test_mcp_request_validation_accepts_report_summary():
    _validate_mcp_arguments(
        "stdio",
        "synthesize_evidence_tool",
        {"drug": "warfarin", "gene": "CYP2C9", "faers_reports": 10, "faers_serious_rate": 0.2},
    )


def test_mcp_dossier_runs_multiple_stages(monkeypatch):
    monkeypatch.setattr("web_server.call_mcp_tool", _fake_mcp_call)
    report = {
        "normalized_query": {"drug": "warfarin", "gene": "CYP2C9", "variant": "rs1799853"},
        "faers": {"status": "ok", "total_reports": 120, "serious_rate": 0.2, "top_reactions": [{"term": "Haemorrhage"}], "source": "faers"},
        "clinvar": {"status": "ok", "total_records": 2, "pathogenic_records": 1, "source": "clinvar", "records": [{"title": "rs1799853", "classification": "Pathogenic", "traits": []}]},
    }
    dossier = build_mcp_dossier(report)
    assert dossier["status"] == "ok"
    assert dossier["workflow"]["total"] == 5
    assert dossier["workflow"]["completed"] == 5
    assert dossier["synthesis"]["details"]["priority"] == "высокий"
    assert dossier["hypotheses"]["details"]["hypotheses"]
