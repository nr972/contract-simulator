from contract_simulator.services.simulator import (
    _extract_tag,
    _parse_clause_analysis,
    _parse_list_items,
    _parse_summary,
    _validate_risk_level,
)


def test_extract_tag():
    text = "<name>hello world</name>"
    assert _extract_tag(text, "name") == "hello world"


def test_extract_tag_multiline():
    text = "<content>\nline 1\nline 2\n</content>"
    assert "line 1" in _extract_tag(text, "content")
    assert "line 2" in _extract_tag(text, "content")


def test_extract_tag_missing():
    assert _extract_tag("no tags here", "name") == ""


def test_parse_list_items():
    text = "- Item 1\n- Item 2\n- Item 3"
    items = _parse_list_items(text)
    assert items == ["Item 1", "Item 2", "Item 3"]


def test_parse_list_items_empty():
    assert _parse_list_items("") == []
    assert _parse_list_items("   ") == []


def test_validate_risk_level():
    assert _validate_risk_level("low") == "low"
    assert _validate_risk_level("medium") == "medium"
    assert _validate_risk_level("high") == "high"
    assert _validate_risk_level("unknown") == "medium"


def test_parse_clause_analysis():
    xml = """<clause_analysis>
<clause_id>clause_1</clause_id>
<clause_title>Confidentiality</clause_title>
<is_triggered>true</is_triggered>
<reasoning>This clause is triggered because...</reasoning>
<triggered_obligations>
- Notify the other party
- Maintain records
</triggered_obligations>
<timelines>
- Within 48 hours
</timelines>
<liability_exposure>Up to $1M</liability_exposure>
<ambiguities>
- Definition of "breach" is vague
</ambiguities>
<risk_level>high</risk_level>
</clause_analysis>"""

    result = _parse_clause_analysis(xml)
    assert result is not None
    assert result.clause_id == "clause_1"
    assert result.clause_title == "Confidentiality"
    assert result.is_triggered is True
    assert len(result.triggered_obligations) == 2
    assert result.timelines == ["Within 48 hours"]
    assert result.liability_exposure == "Up to $1M"
    assert len(result.ambiguities) == 1
    assert result.risk_level == "high"


def test_parse_clause_analysis_not_triggered():
    xml = """<clause_analysis>
<clause_id>clause_2</clause_id>
<clause_title>Force Majeure</clause_title>
<is_triggered>false</is_triggered>
<reasoning>This clause is not triggered.</reasoning>
<triggered_obligations></triggered_obligations>
<timelines></timelines>
<liability_exposure>None</liability_exposure>
<ambiguities></ambiguities>
<risk_level>low</risk_level>
</clause_analysis>"""

    result = _parse_clause_analysis(xml)
    assert result is not None
    assert result.is_triggered is False
    assert result.triggered_obligations == []
    assert result.risk_level == "low"


def test_parse_summary():
    xml = """<summary>
<total_clauses_analyzed>10</total_clauses_analyzed>
<triggered_clauses>4</triggered_clauses>
<key_obligations>
- Notify within 48 hours
- Provide incident report
</key_obligations>
<critical_timelines>
- 48-hour notification
- 5-day incident report
</critical_timelines>
<total_liability_exposure>Up to 2x annual fees</total_liability_exposure>
<high_risk_areas>
- Data protection gaps
</high_risk_areas>
<overall_risk_assessment>Moderate overall risk with specific concerns around notification timing.</overall_risk_assessment>
</summary>"""

    result = _parse_summary(xml)
    assert result is not None
    assert result.total_clauses_analyzed == 10
    assert result.triggered_clauses == 4
    assert len(result.key_obligations) == 2
    assert len(result.critical_timelines) == 2
    assert result.total_liability_exposure == "Up to 2x annual fees"
    assert len(result.high_risk_areas) == 1


def test_parse_clause_analysis_malformed():
    """Malformed input produces an empty-but-valid object (all fields default)."""
    result = _parse_clause_analysis("not xml at all")
    assert result is not None
    assert result.clause_id == ""
    assert result.is_triggered is False
    assert result.triggered_obligations == []


def test_parse_summary_malformed():
    """Malformed input produces an empty-but-valid object (all fields default)."""
    result = _parse_summary("not xml at all")
    assert result is not None
    assert result.total_clauses_analyzed == 0
    assert result.triggered_clauses == 0
