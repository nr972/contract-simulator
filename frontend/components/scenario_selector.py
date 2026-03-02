from typing import Any

import requests
import streamlit as st


def render_scenario_selector(
    api_base: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Render scenario selection and parameter configuration.

    Returns (scenario_dict, parameters_dict) or (None, None) if not ready.
    """
    st.header("Step 2: Select Scenario")

    # Fetch scenarios
    scenarios = _fetch_scenarios(api_base)
    if not scenarios:
        return None, None

    # Scenario dropdown
    scenario_names = {s["name"]: s for s in scenarios}
    selected_name = st.selectbox(
        "Choose a stress-test scenario:",
        options=list(scenario_names.keys()),
        help="Select the scenario to simulate against the uploaded contract.",
    )

    if not selected_name:
        return None, None

    scenario = scenario_names[selected_name]
    st.info(scenario["description"])

    # Parameter inputs
    st.subheader("Scenario Parameters")
    parameters: dict[str, Any] = {}

    for param in scenario["parameters"]:
        param_name = param["name"]
        param_type = param["param_type"]
        description = param["description"]
        default = param.get("default_value")
        options = param.get("options")

        if options:
            parameters[param_name] = st.selectbox(
                description,
                options=options,
                index=options.index(default) if default in options else 0,
                key=f"param_{param_name}",
            )
        elif param_type == "int":
            parameters[param_name] = st.number_input(
                description,
                value=int(default) if default is not None else 0,
                step=1,
                key=f"param_{param_name}",
            )
        elif param_type == "float":
            parameters[param_name] = st.number_input(
                description,
                value=float(default) if default is not None else 0.0,
                key=f"param_{param_name}",
            )
        elif param_type == "bool":
            parameters[param_name] = st.checkbox(
                description,
                value=bool(default) if default is not None else False,
                key=f"param_{param_name}",
            )
        else:  # str
            parameters[param_name] = st.text_input(
                description,
                value=str(default) if default is not None else "",
                key=f"param_{param_name}",
            )

    return scenario, parameters


@st.cache_data(ttl=300)
def _fetch_scenarios(api_base: str) -> list[dict[str, Any]]:
    """Fetch available scenarios from the API."""
    try:
        response = requests.get(f"{api_base}/scenarios", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "Cannot connect to the API server. "
            "Make sure the backend is running on port 8000."
        )
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"Failed to fetch scenarios: {e}")
        return []
