from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from contract_simulator.core.config import Settings, get_settings
from contract_simulator.models.contract import Clause
from contract_simulator.models.scenario import Scenario
from contract_simulator.services.parameter_suggester import suggest_defaults
from contract_simulator.services.scenario_engine import get_scenario, load_scenarios

router = APIRouter()


class SuggestDefaultsRequest(BaseModel):
    clauses: list[Clause]


class SuggestDefaultsResponse(BaseModel):
    defaults: dict[str, Any]


@router.get("", response_model=list[Scenario])
async def list_scenarios(
    settings: Settings = Depends(get_settings),
) -> list[Scenario]:
    """List all available simulation scenarios."""
    return load_scenarios(settings.scenarios_dir)


@router.get("/{scenario_id}", response_model=Scenario)
async def get_scenario_detail(
    scenario_id: str,
    settings: Settings = Depends(get_settings),
) -> Scenario:
    """Get details of a specific scenario including its parameters."""
    return get_scenario(scenario_id, settings.scenarios_dir)


@router.post("/{scenario_id}/suggest-defaults", response_model=SuggestDefaultsResponse)
async def suggest_scenario_defaults(
    scenario_id: str,
    request: SuggestDefaultsRequest,
    settings: Settings = Depends(get_settings),
) -> SuggestDefaultsResponse:
    """Suggest contract-aware parameter defaults for a scenario.

    Analyzes the contract's clauses to extract values relevant to
    the scenario's parameters. Falls back to template defaults
    when no contract-specific value is found.
    """
    scenario = get_scenario(scenario_id, settings.scenarios_dir)
    defaults = await suggest_defaults(request.clauses, scenario, settings)
    return SuggestDefaultsResponse(defaults=defaults)
