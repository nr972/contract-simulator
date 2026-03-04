import logging
import re
from collections.abc import AsyncGenerator

import anthropic

from contract_simulator.core.config import Settings
from contract_simulator.models.contract import ParsedContract
from contract_simulator.models.scenario import Scenario
from contract_simulator.models.simulation import (
    ClauseAnalysis,
    SimulationEvent,
    SimulationSummary,
)
from contract_simulator.prompts.simulation import (
    SIMULATION_SYSTEM,
    build_simulation_prompt,
)

logger = logging.getLogger(__name__)


def _parse_list_items(text: str) -> list[str]:
    """Parse a bulleted list from text, returning non-empty items."""
    items = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("- "):
            line = line[2:].strip()
        if line:
            items.append(line)
    return items


def _extract_tag(text: str, tag: str) -> str:
    """Extract content between XML tags."""
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_clause_analysis(xml_block: str) -> ClauseAnalysis | None:
    """Parse a <clause_analysis> XML block into a ClauseAnalysis object."""
    try:
        return ClauseAnalysis(
            clause_id=_extract_tag(xml_block, "clause_id"),
            clause_title=_extract_tag(xml_block, "clause_title"),
            is_triggered=_extract_tag(xml_block, "is_triggered").lower() == "true",
            reasoning=_extract_tag(xml_block, "reasoning"),
            triggered_obligations=_parse_list_items(
                _extract_tag(xml_block, "triggered_obligations")
            ),
            timelines=_parse_list_items(_extract_tag(xml_block, "timelines")),
            liability_exposure=_extract_tag(xml_block, "liability_exposure") or None,
            ambiguities=_parse_list_items(_extract_tag(xml_block, "ambiguities")),
            risk_level=_validate_risk_level(
                _extract_tag(xml_block, "risk_level").lower()
            ),
        )
    except Exception as e:
        logger.warning("Failed to parse clause analysis block: %s", e)
        return None


def _parse_summary(xml_block: str) -> SimulationSummary | None:
    """Parse a <summary> XML block into a SimulationSummary object."""
    try:
        total_str = _extract_tag(xml_block, "total_clauses_analyzed")
        triggered_str = _extract_tag(xml_block, "triggered_clauses")

        return SimulationSummary(
            total_clauses_analyzed=int(total_str) if total_str.isdigit() else 0,
            triggered_clauses=int(triggered_str) if triggered_str.isdigit() else 0,
            key_obligations=_parse_list_items(
                _extract_tag(xml_block, "key_obligations")
            ),
            critical_timelines=_parse_list_items(
                _extract_tag(xml_block, "critical_timelines")
            ),
            total_liability_exposure=_extract_tag(
                xml_block, "total_liability_exposure"
            ),
            high_risk_areas=_parse_list_items(
                _extract_tag(xml_block, "high_risk_areas")
            ),
            overall_risk_assessment=_extract_tag(
                xml_block, "overall_risk_assessment"
            ),
        )
    except Exception as e:
        logger.warning("Failed to parse summary block: %s", e)
        return None


def _validate_risk_level(value: str) -> str:
    """Validate and normalize risk level to low/medium/high."""
    if value in ("low", "medium", "high"):
        return value
    return "medium"  # Default if parsing fails


def _filter_clauses(
    contract: ParsedContract, scenario: Scenario
) -> list[dict[str, str]]:
    """Filter contract clauses to those relevant to the scenario.

    If the scenario defines relevant_clause_types, only include matching
    clauses. Otherwise, include all clauses.
    """
    relevant_types = set(scenario.relevant_clause_types)

    clauses_data = []
    for c in contract.clauses:
        if relevant_types and c.clause_type not in relevant_types:
            continue
        clauses_data.append(
            {
                "section_number": c.section_number,
                "title": c.title,
                "clause_type": c.clause_type,
                "content": c.content,
            }
        )
    return clauses_data


async def run_simulation(
    contract: ParsedContract,
    scenario: Scenario,
    parameters: dict[str, str | int | float | bool],
    settings: Settings,
) -> AsyncGenerator[SimulationEvent, None]:
    """Run a contract simulation against a scenario, streaming results.

    Filters clauses to those relevant to the scenario, then makes a single
    streaming Claude API call. Yields text_delta events for progressive
    display, plus structured clause_analysis and summary events as XML
    blocks complete.
    """
    clauses_data = _filter_clauses(contract, scenario)

    if not clauses_data:
        yield SimulationEvent(
            event_type="error",
            data="No clauses in this contract are relevant to the selected scenario.",
        )
        return

    prompt = build_simulation_prompt(
        scenario_name=scenario.name,
        scenario_description=scenario.description,
        parameters=parameters,
        analysis_guidance=scenario.analysis_guidance,
        contract_title=contract.contract_title,
        parties=contract.parties,
        effective_date=contract.effective_date,
        clauses=clauses_data,
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    try:
        accumulated = ""

        with client.messages.stream(
            model=settings.anthropic_model,
            max_tokens=8192,
            system=SIMULATION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                accumulated += text

                # Emit text deltas for progressive frontend display
                yield SimulationEvent(event_type="text_delta", data=text)

                # Check for complete clause_analysis blocks
                while "</clause_analysis>" in accumulated:
                    end_idx = accumulated.index("</clause_analysis>") + len(
                        "</clause_analysis>"
                    )
                    start_match = accumulated.find("<clause_analysis>")

                    if start_match == -1:
                        break

                    block = accumulated[start_match:end_idx]
                    accumulated = accumulated[end_idx:]

                    analysis = _parse_clause_analysis(block)
                    if analysis:
                        yield SimulationEvent(
                            event_type="clause_analysis", data=analysis
                        )

                # Check for complete summary block
                if "</summary>" in accumulated:
                    start_match = accumulated.find("<summary>")
                    if start_match != -1:
                        end_idx = accumulated.index("</summary>") + len("</summary>")
                        block = accumulated[start_match:end_idx]
                        accumulated = accumulated[end_idx:]

                        summary = _parse_summary(block)
                        if summary:
                            yield SimulationEvent(
                                event_type="summary", data=summary
                            )

    except anthropic.APIError as e:
        logger.error("Anthropic API error during simulation: %s", e)
        yield SimulationEvent(
            event_type="error",
            data="Failed to communicate with the AI service. Please try again.",
        )
    except Exception as e:
        logger.error("Unexpected error during simulation: %s", e)
        yield SimulationEvent(
            event_type="error",
            data="An unexpected error occurred during simulation.",
        )
