from fastapi import APIRouter, Depends

from contract_simulator.core.config import Settings, get_settings
from contract_simulator.models.scenario import Scenario
from contract_simulator.services.scenario_engine import get_scenario, load_scenarios

router = APIRouter()


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
