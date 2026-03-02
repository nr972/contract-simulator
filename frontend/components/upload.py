from pathlib import Path
from typing import Any

import requests
import streamlit as st


def render_upload(api_base: str) -> dict[str, Any] | None:
    """Render the contract upload section and return parsed contract data."""
    st.header("Step 1: Upload Contract")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Upload a contract (PDF or DOCX)",
            type=["pdf", "docx"],
            help="Maximum file size: 10MB",
        )

    with col2:
        st.markdown("**Or try a sample:**")
        sample_dir = Path("data/sample")
        sample_files = sorted(sample_dir.glob("*")) if sample_dir.exists() else []

        for sample_file in sample_files:
            if st.button(f"Load {sample_file.stem}", key=f"sample_{sample_file.name}"):
                st.session_state["sample_file"] = sample_file

    # Determine which file to parse
    file_to_parse = None
    file_name = None

    if uploaded_file is not None:
        file_to_parse = uploaded_file.getvalue()
        file_name = uploaded_file.name
    elif "sample_file" in st.session_state:
        sample_path = st.session_state["sample_file"]
        file_to_parse = sample_path.read_bytes()
        file_name = sample_path.name

    if file_to_parse is None:
        return None

    # Check cache
    cache_key = f"parsed_{file_name}"
    if cache_key in st.session_state:
        _display_parsed_contract(st.session_state[cache_key])
        return st.session_state[cache_key]

    # Parse the contract
    with st.spinner("Parsing contract with AI... This may take a moment."):
        try:
            response = requests.post(
                f"{api_base}/contracts/parse",
                files={"file": (file_name, file_to_parse)},
                timeout=120,
            )
            response.raise_for_status()
            parsed = response.json()
            st.session_state[cache_key] = parsed
            _display_parsed_contract(parsed)
            return parsed
        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to the API server. "
                "Make sure the backend is running on port 8000."
            )
            return None
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                detail = e.response.json().get("detail", "")
            except Exception:
                pass
            st.error(f"Failed to parse contract: {detail or str(e)}")
            return None
        except requests.exceptions.Timeout:
            st.error("Request timed out. The contract may be too large. Please try again.")
            return None


def _display_parsed_contract(parsed: dict) -> None:
    """Display the parsed contract details."""
    st.success(
        f"Parsed: **{parsed['contract_title']}** — "
        f"{len(parsed['clauses'])} clauses identified"
    )

    with st.expander("View parsed clauses", expanded=False):
        for clause in parsed["clauses"]:
            st.markdown(
                f"**[{clause['section_number']}] {clause['title']}** "
                f"({clause['clause_type']})"
            )
            st.caption(
                clause["content"][:300]
                + ("..." if len(clause["content"]) > 300 else "")
            )
            st.markdown("---")
