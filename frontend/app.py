import streamlit as st
import streamlit.components.v1 as components

from components.upload import render_upload
from components.scenario_selector import render_scenario_selector
from components.walkthrough import render_walkthrough

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Contract Simulator",
    page_icon="📋",
    layout="wide",
)

# --- Sidebar: Shutdown button ---
with st.sidebar:
    st.markdown("---")
    if st.button("Shutdown App", type="secondary"):
        import requests

        try:
            requests.post(f"{API_BASE}/api/v1/shutdown", timeout=2)
        except Exception:
            pass  # Server may already be dying

        # Replace the entire parent document before Streamlit detects
        # the lost websocket connection and shows its reconnection UI.
        components.html(
            """
            <script>
            (function() {
                try {
                    var doc = window.top.document;
                    doc.open();
                    doc.write(
                        '<!DOCTYPE html>' +
                        '<html><head><title>Contract Simulator</title></head>' +
                        '<body style="margin:0;display:flex;align-items:center;' +
                        'justify-content:center;height:100vh;' +
                        'font-family:-apple-system,BlinkMacSystemFont,sans-serif;' +
                        'background:#f8f9fa;color:#333;">' +
                        '<div style="text-align:center;padding:2rem;">' +
                        '<h1 style="font-size:1.5rem;margin-bottom:1rem;">' +
                        'App has been shut down.</h1>' +
                        '<p style="color:#666;">You can close this tab.</p>' +
                        '</div></body></html>'
                    );
                    doc.close();
                } catch(e) {
                    document.body.innerHTML =
                        '<p style="padding:1rem;">App has been shut down. ' +
                        'You can close this tab.</p>';
                }
            })();
            </script>
            """,
            height=0,
        )
        st.stop()

# --- Main content ---
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
