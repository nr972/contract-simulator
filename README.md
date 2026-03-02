# Contract Simulator & Stress-Tester

Simulate how contract clauses play out under real-world scenarios. Upload a contract, select a stress-test scenario, and get a clause-by-clause walkthrough showing triggered obligations, timelines, liabilities, and risk areas.

## Getting Started

### Option 1: Hosted Version

> Coming soon — a hosted version will be available at a public URL.

### Option 2: Run Locally (One Command)

**macOS / Linux:**
```bash
./start.sh
```

**Windows:**
```
start.bat
```

The script will set up everything automatically (Python virtual environment, dependencies) and open the app in your browser. You'll need an [Anthropic API key](https://console.anthropic.com/) — the script will prompt you for it on first run.

### Option 3: Docker

```bash
# Create a .env file with your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Start all services
docker compose up
```

Then open http://localhost:8501 in your browser.

## Deploy Your Own

### Railway (One-Click Cloud Deploy)

1. Fork this repo on GitHub
2. Sign up at [Railway](https://railway.app)
3. Create a new project from your fork
4. Add the environment variable `ANTHROPIC_API_KEY` in Railway's settings
5. Deploy — Railway will build and launch automatically

## Features

- **Contract Parsing** — Upload PDF or DOCX contracts. AI identifies and categorizes every clause.
- **5 Stress-Test Scenarios:**
  - Data Breach (notification obligations, liability caps, indemnification)
  - Service Outage (SLA credits, termination rights, remediation)
  - Termination for Convenience (notice periods, wind-down, survival clauses)
  - IP Ownership Dispute (ownership, licensing, assignment)
  - Force Majeure (qualification, mitigation, extended event termination)
- **Clause-by-Clause Walkthrough** — Step-by-step analysis with chain-of-thought reasoning
- **Risk Assessment** — Color-coded risk levels (low/medium/high) per clause and overall
- **Streaming Results** — See analysis in real-time as each clause is processed

## For Developers

### API Documentation

With the API running, visit http://localhost:8000/docs for interactive Swagger documentation.

**Key endpoints:**
- `POST /contracts/parse` — Upload and parse a contract
- `GET /scenarios` — List available scenarios
- `POST /simulations/run` — Run simulation (returns SSE stream)

### Project Structure

```
src/contract_simulator/
├── api/           # FastAPI routes and app
├── core/          # Config and security
├── models/        # Pydantic data models
├── services/      # Business logic (parsing, simulation)
└── prompts/       # LLM prompt templates

frontend/          # Streamlit UI
data/scenarios/    # Scenario template definitions (JSON)
data/sample/       # Synthetic sample contracts
tests/             # pytest test suite
```

### Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

### Tech Stack

- **Backend:** Python 3.11+, FastAPI
- **LLM:** Anthropic Claude (Sonnet 4.6)
- **Document Parsing:** python-docx, pdfplumber
- **Frontend:** Streamlit
- **Deployment:** Docker, Railway

## License

MIT — Copyright (c) 2026 Noam Raz and Pleasant Secret Labs
