#!/usr/bin/env bash
set -e

# Start FastAPI in background
uvicorn src.contract_simulator.api.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit (foreground)
streamlit run cs_frontend/app.py \
    --server.port 8501 \
    --server.headless true \
    --server.address 0.0.0.0 \
    --server.enableCORS false \
    --server.enableXsrfProtection false
