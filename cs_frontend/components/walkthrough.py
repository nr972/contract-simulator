import json
from typing import Any

import httpx
import streamlit as st

RISK_COLORS = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🔴",
}


def render_walkthrough(
    api_base: str,
    parsed_contract: dict[str, Any],
    scenario: dict[str, Any],
    parameters: dict[str, Any],
) -> None:
    """Render the simulation walkthrough with streaming results."""
    st.header("Step 3: Simulation Results")

    if not st.button("Run Simulation", type="primary"):
        return

    request_body = {
        "parsed_contract": parsed_contract,
        "scenario_id": scenario["id"],
        "parameters": parameters,
    }

    clause_analyses: list[dict[str, Any]] = []
    summary_data: dict[str, Any] | None = None
    error_message: str | None = None

    progress_placeholder = st.empty()
    live_text_placeholder = st.empty()
    results_container = st.container()

    with progress_placeholder.container():
        st.info(
            f"Simulating **{scenario['name']}** scenario... "
            "Live analysis will appear below."
        )

    # Accumulate raw text for progressive display
    live_text = ""

    # Stream results from SSE endpoint
    try:
        with httpx.Client(timeout=300) as client:
            with client.stream(
                "POST",
                f"{api_base}/simulations/run",
                json=request_body,
            ) as response:
                response.raise_for_status()

                buffer = ""
                for chunk in response.iter_text():
                    buffer += chunk
                    while "\n\n" in buffer:
                        event_str, buffer = buffer.split("\n\n", 1)
                        event_str = event_str.strip()
                        if not event_str.startswith("data: "):
                            continue
                        json_str = event_str[6:]

                        try:
                            event = json.loads(json_str)
                        except json.JSONDecodeError:
                            continue

                        if event["event_type"] == "text_delta":
                            live_text += event["data"]
                            # Strip XML tags for display
                            display_text = _strip_xml_tags(live_text)
                            if display_text.strip():
                                live_text_placeholder.markdown(
                                    f"```\n{display_text[-2000:]}\n```"
                                )

                        elif event["event_type"] == "clause_analysis":
                            clause_analyses.append(event["data"])
                            progress_placeholder.info(
                                f"Analyzed {len(clause_analyses)} clause(s)... "
                                f"Latest: {event['data']['clause_title']}"
                            )

                        elif event["event_type"] == "summary":
                            summary_data = event["data"]

                        elif event["event_type"] == "error":
                            error_message = event["data"]

    except httpx.ConnectError:
        st.error(
            "Cannot connect to the API server. "
            "Make sure the backend is running on port 8000."
        )
        return
    except httpx.HTTPStatusError as e:
        st.error(f"Simulation failed: {e}")
        return
    except httpx.ReadTimeout:
        st.error("Simulation timed out. The contract may be too large.")
        return

    # Clear progress indicators
    progress_placeholder.empty()
    live_text_placeholder.empty()

    if error_message:
        st.error(f"Simulation error: {error_message}")
        return

    # Display structured results
    with results_container:
        _display_clause_analyses(clause_analyses)
        if summary_data:
            _display_summary(summary_data)


def _strip_xml_tags(text: str) -> str:
    """Strip XML tags from text for readable live display."""
    import re

    # Remove XML tags but keep content
    clean = re.sub(r"<[^>]+>", "", text)
    # Collapse multiple blank lines
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean.strip()


def _display_clause_analyses(analyses: list[dict[str, Any]]) -> None:
    """Display clause-by-clause analysis results."""
    st.subheader("Clause-by-Clause Analysis")

    triggered = [a for a in analyses if a["is_triggered"]]
    not_triggered = [a for a in analyses if not a["is_triggered"]]

    if triggered:
        st.markdown(f"**{len(triggered)} clause(s) triggered** out of {len(analyses)} analyzed")

    for analysis in triggered + not_triggered:
        risk_icon = RISK_COLORS.get(analysis["risk_level"], "⚪")
        triggered_label = "TRIGGERED" if analysis["is_triggered"] else "Not triggered"

        with st.expander(
            f"{risk_icon} [{analysis['clause_id']}] {analysis['clause_title']} — {triggered_label}",
            expanded=analysis["is_triggered"],
        ):
            st.markdown("**Analysis:**")
            st.markdown(analysis["reasoning"])

            if analysis["is_triggered"]:
                col1, col2 = st.columns(2)

                with col1:
                    if analysis["triggered_obligations"]:
                        st.markdown("**Triggered Obligations:**")
                        for obligation in analysis["triggered_obligations"]:
                            st.markdown(f"- {obligation}")

                    if analysis["timelines"]:
                        st.markdown("**Timelines:**")
                        for timeline in analysis["timelines"]:
                            st.markdown(f"- {timeline}")

                with col2:
                    if analysis["liability_exposure"]:
                        st.markdown("**Liability Exposure:**")
                        st.markdown(analysis["liability_exposure"])

                    if analysis["ambiguities"]:
                        st.markdown("**Ambiguities & Gaps:**")
                        for ambiguity in analysis["ambiguities"]:
                            st.markdown(f"- {ambiguity}")


def _display_summary(summary: dict[str, Any]) -> None:
    """Display the overall simulation summary."""
    st.divider()
    st.subheader("Overall Assessment")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Clauses Analyzed", summary["total_clauses_analyzed"])
    with col2:
        st.metric("Clauses Triggered", summary["triggered_clauses"])
    with col3:
        st.metric(
            "Trigger Rate",
            f"{summary['triggered_clauses']}/{summary['total_clauses_analyzed']}",
        )

    col_left, col_right = st.columns(2)

    with col_left:
        if summary["key_obligations"]:
            st.markdown("**Key Obligations:**")
            for item in summary["key_obligations"]:
                st.markdown(f"- {item}")

        if summary["critical_timelines"]:
            st.markdown("**Critical Timelines:**")
            for item in summary["critical_timelines"]:
                st.markdown(f"- {item}")

    with col_right:
        if summary["total_liability_exposure"]:
            st.markdown("**Total Liability Exposure:**")
            st.markdown(summary["total_liability_exposure"])

        if summary["high_risk_areas"]:
            st.markdown("**High Risk Areas:**")
            for item in summary["high_risk_areas"]:
                st.markdown(f"- {item}")

    if summary["overall_risk_assessment"]:
        st.divider()
        st.markdown("**Overall Risk Assessment:**")
        st.markdown(summary["overall_risk_assessment"])
