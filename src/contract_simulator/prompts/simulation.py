SIMULATION_SYSTEM = """You are a senior legal analyst conducting a contract stress test. Your role \
is to analyze each clause of a contract against a specific scenario and identify the contractual \
consequences with precision and transparency.

You must think step by step through each clause, applying the scenario facts to determine what \
obligations, rights, and risks arise. Be specific — cite clause language where relevant. Flag \
ambiguities and gaps honestly.

IMPORTANT: Structure your output using the XML tags described below. Each clause analysis and the \
final summary must be wrapped in the specified tags so they can be parsed programmatically."""

SIMULATION_USER = """## Scenario: {scenario_name}

{scenario_description}

### Scenario Parameters:
{scenario_parameters}

### Analysis Guidance:
{analysis_guidance}

---

## Contract: {contract_title}

**Parties:** {parties}
{effective_date_line}

### Clauses to Analyze:

{clauses_text}

---

## Instructions

Analyze EACH clause above against the scenario. For each clause, wrap your analysis in XML tags \
as follows:

<clause_analysis>
<clause_id>clause_1</clause_id>
<clause_title>Title of the clause</clause_title>
<is_triggered>true or false</is_triggered>
<reasoning>Your step-by-step chain-of-thought analysis of how this clause applies to the \
scenario. Be specific and cite clause language.</reasoning>
<triggered_obligations>
- Obligation 1
- Obligation 2
</triggered_obligations>
<timelines>
- Timeline 1 (e.g., "Notify within 72 hours of discovery")
</timelines>
<liability_exposure>Description of liability exposure, or "None" if not applicable</liability_exposure>
<ambiguities>
- Ambiguity or gap 1
- Ambiguity or gap 2
</ambiguities>
<risk_level>low, medium, or high</risk_level>
</clause_analysis>

After analyzing ALL clauses, provide an overall summary:

<summary>
<total_clauses_analyzed>N</total_clauses_analyzed>
<triggered_clauses>N</triggered_clauses>
<key_obligations>
- Key obligation 1
- Key obligation 2
</key_obligations>
<critical_timelines>
- Critical timeline 1
- Critical timeline 2
</critical_timelines>
<total_liability_exposure>Overall liability exposure assessment</total_liability_exposure>
<high_risk_areas>
- High risk area 1
- High risk area 2
</high_risk_areas>
<overall_risk_assessment>A concise overall risk assessment paragraph</overall_risk_assessment>
</summary>

Begin your analysis now. Analyze every clause — do not skip any."""


def build_simulation_prompt(
    scenario_name: str,
    scenario_description: str,
    parameters: dict[str, str | int | float | bool],
    analysis_guidance: str,
    contract_title: str,
    parties: list[str],
    effective_date: str | None,
    clauses: list[dict[str, str]],
) -> str:
    """Build the full simulation prompt from components."""
    # Format parameters
    params_lines = "\n".join(f"- **{k}:** {v}" for k, v in parameters.items())

    # Format effective date
    effective_date_line = (
        f"**Effective Date:** {effective_date}" if effective_date else ""
    )

    # Format clauses
    clauses_parts = []
    for clause in clauses:
        clauses_parts.append(
            f"**[{clause['section_number']}] {clause['title']}** "
            f"(Type: {clause['clause_type']})\n{clause['content']}"
        )
    clauses_text = "\n\n---\n\n".join(clauses_parts)

    return SIMULATION_USER.format(
        scenario_name=scenario_name,
        scenario_description=scenario_description,
        scenario_parameters=params_lines,
        analysis_guidance=analysis_guidance,
        contract_title=contract_title,
        parties=", ".join(parties),
        effective_date_line=effective_date_line,
        clauses_text=clauses_text,
    )
