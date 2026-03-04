from typing import Any

import requests
import streamlit as st


def render_scenario_selector(
    api_base: str,
    parsed_contract: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Render scenario selection and parameter configuration.

    If parsed_contract is provided, fetches contract-aware default values
    for the selected scenario's parameters.

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

    # Get smart defaults if we have a parsed contract
    smart_defaults = _get_smart_defaults(
        api_base, scenario, parsed_contract
    )

    # Parameter inputs
    st.subheader("Scenario Parameters")
    parameters: dict[str, Any] = {}

    for param in scenario["parameters"]:
        param_name = param["name"]
        param_type = param["param_type"]
        description = param["description"]
        options = param.get("options")

        # Use smart default if available, otherwise template default
        template_default = param.get("default_value")
        default = smart_defaults.get(param_name, template_default)
        is_smart = (
            smart_defaults is not None
            and param_name in smart_defaults
            and smart_defaults[param_name] != template_default
        )

        if options:
            index = options.index(str(default)) if str(default) in options else 0
            parameters[param_name] = st.selectbox(
                description,
                options=options,
                index=index,
                key=f"param_{param_name}",
                help="Extracted from contract" if is_smart else None,
            )
        elif param_type == "int":
            parameters[param_name] = st.number_input(
                description,
                value=int(default) if default is not None else 0,
                step=1,
                key=f"param_{param_name}",
                help="Extracted from contract" if is_smart else None,
            )
        elif param_type == "float":
            parameters[param_name] = st.number_input(
                description,
                value=float(default) if default is not None else 0.0,
                key=f"param_{param_name}",
                help="Extracted from contract" if is_smart else None,
            )
        elif param_type == "bool":
            parameters[param_name] = st.checkbox(
                description,
                value=bool(default) if default is not None else False,
                key=f"param_{param_name}",
                help="Extracted from contract" if is_smart else None,
            )
        else:  # str
            parameters[param_name] = st.text_input(
                description,
                value=str(default) if default is not None else "",
                key=f"param_{param_name}",
                help="Extracted from contract" if is_smart else None,
            )

    return scenario, parameters


def _get_smart_defaults(
    api_base: str,
    scenario: dict[str, Any],
    parsed_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    """Fetch contract-aware defaults for scenario parameters.

    Returns smart defaults dict, or empty dict if unavailable.
    Caches per scenario+contract combo in session state.
    """
    if not parsed_contract or not parsed_contract.get("clauses"):
        return {}

    # Cache key based on scenario ID and contract title
    cache_key = f"smart_defaults_{scenario['id']}_{parsed_contract.get('contract_title', '')}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    try:
        response = requests.post(
            f"{api_base}/scenarios/{scenario['id']}/suggest-defaults",
            json={"clauses": parsed_contract["clauses"]},
            timeout=30,
        )
        response.raise_for_status()
        defaults = response.json().get("defaults", {})
        st.session_state[cache_key] = defaults
        return defaults
    except Exception:
        st.session_state[cache_key] = {}
        return {}


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
