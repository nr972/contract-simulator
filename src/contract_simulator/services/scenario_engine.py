import json
import logging
from pathlib import Path

from fastapi import HTTPException, status

from contract_simulator.models.scenario import Scenario

logger = logging.getLogger(__name__)

_scenarios_cache: dict[str, Scenario] | None = None


def _load_scenarios_from_dir(scenarios_dir: str) -> dict[str, Scenario]:
    """Load all scenario JSON files from the given directory."""
    scenarios: dict[str, Scenario] = {}
    path = Path(scenarios_dir)

    if not path.is_dir():
        logger.warning("Scenarios directory not found: %s", scenarios_dir)
        return scenarios

    for file_path in sorted(path.glob("*.json")):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            scenario = Scenario(**data)
            scenarios[scenario.id] = scenario
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to load scenario from %s: %s", file_path, e)

    return scenarios


def load_scenarios(scenarios_dir: str) -> list[Scenario]:
    """Load all available scenarios. Results are cached after first load."""
    global _scenarios_cache
    if _scenarios_cache is None:
        _scenarios_cache = _load_scenarios_from_dir(scenarios_dir)
    return list(_scenarios_cache.values())


def get_scenario(scenario_id: str, scenarios_dir: str) -> Scenario:
    """Get a specific scenario by ID."""
    global _scenarios_cache
    if _scenarios_cache is None:
        _scenarios_cache = _load_scenarios_from_dir(scenarios_dir)

    scenario = _scenarios_cache.get(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found.",
        )
    return scenario


def validate_scenario_parameters(
    scenario: Scenario, parameters: dict[str, str | int | float | bool]
) -> dict[str, str | int | float | bool]:
    """Validate and fill in default values for scenario parameters.

    Returns the validated parameter dict with defaults applied.
    """
    validated: dict[str, str | int | float | bool] = {}

    for param in scenario.parameters:
        value = parameters.get(param.name)

        if value is None:
            if param.default_value is not None:
                value = param.default_value
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required parameter: {param.name}",
                )

        # Validate options if defined
        if param.options and str(value) not in param.options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid value for '{param.name}': '{value}'. "
                    f"Allowed: {', '.join(param.options)}"
                ),
            )

        validated[param.name] = value

    return validated


def clear_cache() -> None:
    """Clear the scenario cache. Useful for testing."""
    global _scenarios_cache
    _scenarios_cache = None
