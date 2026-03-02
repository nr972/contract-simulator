import streamlit as st

from components.upload import render_upload
from components.scenario_selector import render_scenario_selector
from components.walkthrough import render_walkthrough

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Contract Simulator",
    page_icon="📋",
    layout="wide",
)

st.title("Contract Simulator & Stress-Tester")
st.markdown(
    "Upload a contract, select a scenario, and simulate how clauses play out "
    "under real-world conditions."
)
st.divider()

# Step 1: Upload and parse contract
parsed_contract = render_upload(API_BASE)

if parsed_contract:
    st.divider()

    # Step 2: Select and configure scenario
    scenario, parameters = render_scenario_selector(API_BASE)

    if scenario and parameters is not None:
        st.divider()

        # Step 3: Run simulation and display walkthrough
        render_walkthrough(API_BASE, parsed_contract, scenario, parameters)
