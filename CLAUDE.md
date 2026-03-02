# Contract Simulator — CLAUDE.md

## Project Overview

Contract Simulation & Stress-Tester: upload a contract (PDF/DOCX), select a scenario (data breach, service outage, termination, IP dispute, force majeure), and get a streaming clause-by-clause walkthrough showing triggered obligations, timelines, liabilities, and ambiguities. Portfolio capstone for the legal quant project series.

See `PORTFOLIO_STANDARDS.md` for cross-portfolio patterns (README structure, deployment tiers, audience guidelines).

## Tech Stack

- **Backend:** Python 3.11+, FastAPI
- **LLM:** Anthropic Claude Sonnet 4.6 (`claude-sonnet-4-6`) via `anthropic` SDK
- **Document parsing:** python-docx (DOCX), pdfplumber (PDF)
- **Validation:** Pydantic v2
- **Frontend:** Streamlit (thin client calling API via HTTP)
- **Testing:** pytest
- **Package management:** pyproject.toml (PEP 621)
- **Deployment:** Docker + Railway

## Architecture

**API-first.** FastAPI handles all logic. Streamlit is a thin HTTP client.

- `POST /contracts/parse` — upload + parse contract into structured clauses
- `GET /scenarios` / `GET /scenarios/{id}` — list/get scenario templates
- `POST /simulations/run` — run simulation, returns SSE stream
- `GET /health` — health check

**No database.** All processing is transient/in-memory. No persistence.

**Streaming.** Simulation results stream via SSE (Server-Sent Events). Claude's output uses XML-tagged sections (`<clause_analysis>`, `<summary>`) parsed during streaming into structured `SimulationEvent` objects.

## Directory Structure

```
src/contract_simulator/
├── api/main.py                  # FastAPI app factory
├── api/routes/contracts.py      # Contract upload/parse endpoint
├── api/routes/scenarios.py      # Scenario listing endpoints
├── api/routes/simulations.py    # Simulation SSE endpoint
├── core/config.py               # Pydantic BaseSettings
├── core/security.py             # File upload validation
├── models/contract.py           # ParsedContract, Clause
├── models/scenario.py           # Scenario, ScenarioParameter
├── models/simulation.py         # SimulationRequest/Event/Summary
├── services/parser.py           # PDF/DOCX text extraction
├── services/clause_extractor.py # Claude clause structuring
├── services/scenario_engine.py  # Scenario template loading
├── services/simulator.py        # Core simulation + streaming
├── prompts/clause_extraction.py # Clause extraction prompts
└── prompts/simulation.py        # Simulation analysis prompts

frontend/
├── app.py                       # Streamlit main app
└── components/                  # Upload, scenario selector, walkthrough

data/
├── sample/                      # Synthetic sample contracts
└── scenarios/                   # Predefined scenario JSON templates

tests/                           # pytest test suite
```

## Coding Conventions

- Type hints on all function signatures
- Pydantic v2 for all request/response models
- FastAPI dependency injection for shared resources
- Keep modules small and focused
- No over-engineering — minimum complexity for the current task
- Async functions for I/O-bound operations (Claude API calls, file parsing)

## Security Policy

- **File uploads:** Validate extension (`.pdf`, `.docx`), file size (10MB limit), and magic bytes before processing
- **No persistence:** Uploaded files are processed in-memory via BytesIO, never written to disk
- **API keys:** Anthropic API key via `ANTHROPIC_API_KEY` env var only, never in code
- **Input sanitization:** Validate all user-provided scenario parameters against type definitions
- **No shell execution:** Never execute user input as shell commands
- **Path traversal:** Sanitize filenames, reject any path separators
- **Error messages:** Never expose internal stack traces or file paths to users
- **CORS:** Permissive for dev (localhost), restrictive for production

## Key Commands

```bash
# Run API server
uvicorn src.contract_simulator.api.main:app --reload --port 8000

# Run Streamlit frontend
streamlit run frontend/app.py

# Run tests
pytest tests/

# One-command launch (both services)
./start.sh        # macOS/Linux
start.bat         # Windows

# Docker
docker compose up
```

## License

MIT — Copyright (c) 2026 Noam Raz and Pleasant Secret Labs
