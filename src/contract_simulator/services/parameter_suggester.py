import json
import logging
from typing import Any

import anthropic

from contract_simulator.core.config import Settings
from contract_simulator.models.contract import Clause
from contract_simulator.models.scenario import Scenario
from contract_simulator.prompts.parameter_suggestions import (
    PARAMETER_SUGGESTION_SYSTEM,
    build_parameter_suggestion_prompt,
)

logger = logging.getLogger(__name__)


def _get_template_defaults(scenario: Scenario) -> dict[str, Any]:
    """Extract template default values from a scenario's parameter definitions."""
    defaults: dict[str, Any] = {}
    for param in scenario.parameters:
        if param.default_value is not None:
            defaults[param.name] = param.default_value
    return defaults


async def suggest_defaults(
    clauses: list[Clause],
    scenario: Scenario,
    settings: Settings,
) -> dict[str, Any]:
    """Suggest contract-aware parameter defaults by analyzing clauses with Claude.

    Returns a dict of parameter names to suggested values. Template defaults
    are used as the base; Claude suggestions override where provided.
    Falls back to template defaults entirely if the Claude call fails.
    """
    template_defaults = _get_template_defaults(scenario)

    if not clauses:
        return template_defaults

    # Build prompt inputs
    params_data = [
        {
            "name": p.name,
            "param_type": p.param_type,
            "description": p.description,
            "options": p.options,
        }
        for p in scenario.parameters
    ]
    clauses_data = [
        {
            "section_number": c.section_number,
            "title": c.title,
            "clause_type": c.clause_type,
            "content": c.content,
        }
        for c in clauses
    ]

    prompt = build_parameter_suggestion_prompt(params_data, clauses_data)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    try:
        message = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=PARAMETER_SUGGESTION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text

        # Strip markdown code fences if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            lines = [line for line in lines[1:] if line.strip() != "```"]
            response_text = "\n".join(lines)

        suggestions = json.loads(response_text)

        if not isinstance(suggestions, dict):
            logger.warning("Claude returned non-dict suggestions: %s", type(suggestions))
            return template_defaults

        # Validate suggested values against parameter options
        valid_params = {p.name: p for p in scenario.parameters}
        validated_suggestions: dict[str, Any] = {}

        for key, value in suggestions.items():
            if key not in valid_params:
                continue
            param = valid_params[key]
            # If param has fixed options, validate the suggestion
            if param.options and str(value) not in param.options:
                continue
            validated_suggestions[key] = value

        # Merge: template defaults as base, Claude suggestions override
        merged = {**template_defaults, **validated_suggestions}
        return merged

    except (json.JSONDecodeError, anthropic.APIError, Exception) as e:
        logger.warning("Parameter suggestion failed, using template defaults: %s", e)
        return template_defaults
