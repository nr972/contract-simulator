PARAMETER_SUGGESTION_SYSTEM = """You are a legal contract analyst. Given a contract's clauses \
and a scenario's parameter definitions, extract concrete values from the contract text to \
suggest as parameter defaults.

Return valid JSON only — no markdown, no explanation outside the JSON."""

PARAMETER_SUGGESTION_USER = """Given the contract clauses below and the scenario parameter \
definitions, extract values from the contract text that would be appropriate defaults for \
each parameter.

IMPORTANT: Only include a parameter in your response if you find CLEAR EVIDENCE in the \
contract text. If a parameter's value cannot be determined from the contract, omit it entirely \
so the generic default will be used instead.

For parameters with fixed options, only return values from the allowed options list.

## Scenario Parameters:
{parameters_json}

## Contract Clauses:
{clauses_text}

Return a JSON object mapping parameter names to suggested values. Example:
{{"sla_threshold_hours": 4, "records_affected": 50000}}

Only include parameters where the contract provides clear evidence for a specific value."""


def build_parameter_suggestion_prompt(
    parameters: list[dict],
    clauses: list[dict],
) -> str:
    """Build the prompt for parameter default suggestions."""
    import json

    # Format parameters as concise definitions
    params_for_prompt = []
    for p in parameters:
        entry = {
            "name": p["name"],
            "type": p["param_type"],
            "description": p["description"],
        }
        if p.get("options"):
            entry["allowed_options"] = p["options"]
        params_for_prompt.append(entry)

    # Format clauses — just title, type, and content (no raw_text)
    clauses_parts = []
    for c in clauses:
        clauses_parts.append(
            f"**[{c['section_number']}] {c['title']}** ({c['clause_type']})\n"
            f"{c['content']}"
        )

    return PARAMETER_SUGGESTION_USER.format(
        parameters_json=json.dumps(params_for_prompt, indent=2),
        clauses_text="\n\n---\n\n".join(clauses_parts),
    )
