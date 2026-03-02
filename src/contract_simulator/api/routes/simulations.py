import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from contract_simulator.core.config import Settings, get_settings
from contract_simulator.models.simulation import SimulationRequest
from contract_simulator.services.scenario_engine import (
    get_scenario,
    validate_scenario_parameters,
)
from contract_simulator.services.simulator import run_simulation

router = APIRouter()


@router.post("/run")
async def run_simulation_endpoint(
    request: SimulationRequest,
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """Run a contract simulation against a scenario.

    Returns a Server-Sent Events stream of simulation results.
    Each event is a JSON-serialized SimulationEvent.
    """
    scenario = get_scenario(request.scenario_id, settings.scenarios_dir)
    validated_params = validate_scenario_parameters(scenario, request.parameters)

    async def event_stream():
        async for event in run_simulation(
            contract=request.parsed_contract,
            scenario=scenario,
            parameters=validated_params,
            settings=settings,
        ):
            yield f"data: {json.dumps(event.model_dump())}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
