import pytest
from fastapi import HTTPException

from contract_simulator.services.scenario_engine import (
    clear_cache,
    get_scenario,
    load_scenarios,
    validate_scenario_parameters,
)


@pytest.fixture(autouse=True)
def _clear_scenario_cache():
    """Clear scenario cache before each test."""
    clear_cache()
    yield
    clear_cache()


def test_load_scenarios(settings):
    scenarios = load_scenarios(settings.scenarios_dir)
    assert len(scenarios) == 6

    ids = {s.id for s in scenarios}
    assert "data_breach" in ids
    assert "service_outage" in ids
    assert "termination_for_convenience" in ids
    assert "ip_dispute" in ids
    assert "force_majeure" in ids
    assert "change_of_control" in ids


def test_get_scenario(settings):
    scenario = get_scenario("data_breach", settings.scenarios_dir)
    assert scenario.name == "Data Breach"
    assert len(scenario.parameters) > 0


def test_get_scenario_not_found(settings):
    with pytest.raises(HTTPException) as exc_info:
        get_scenario("nonexistent", settings.scenarios_dir)
    assert exc_info.value.status_code == 404


def test_load_scenarios_missing_dir():
    scenarios = load_scenarios("/nonexistent/path")
    assert scenarios == []


def test_validate_scenario_parameters_defaults(settings):
    scenario = get_scenario("data_breach", settings.scenarios_dir)
    # With no parameters, defaults should be applied
    validated = validate_scenario_parameters(scenario, {})
    assert "records_affected" in validated
    assert validated["records_affected"] == 10000


def test_validate_scenario_parameters_custom(settings):
    scenario = get_scenario("data_breach", settings.scenarios_dir)
    validated = validate_scenario_parameters(
        scenario, {"records_affected": 50000, "data_types": "PHI"}
    )
    assert validated["records_affected"] == 50000
    assert validated["data_types"] == "PHI"


def test_validate_scenario_parameters_invalid_option(settings):
    scenario = get_scenario("data_breach", settings.scenarios_dir)
    with pytest.raises(HTTPException) as exc_info:
        validate_scenario_parameters(
            scenario, {"breach_source": "invalid_source"}
        )
    assert exc_info.value.status_code == 400


def test_scenario_has_analysis_guidance(settings):
    scenario = get_scenario("data_breach", settings.scenarios_dir)
    assert len(scenario.analysis_guidance) > 50
