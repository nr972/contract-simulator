#!/usr/bin/env bash
set -e

# Contract Simulator — One-command launcher
# Usage: ./start.sh

API_PORT=8000
FRONTEND_PORT=8501

echo "========================================="
echo "  Contract Simulator & Stress-Tester"
echo "========================================="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    echo "Install Python from https://python.org or via your package manager."
    exit 1
fi

PYTHON=$(command -v python3)
echo "Using Python: $($PYTHON --version)"

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies (first run only)..."
    pip install -q .
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "No .env file found. Creating one..."
    echo "You need an Anthropic API key to use this tool."
    echo "Get one at: https://console.anthropic.com/"
    echo ""
    read -p "Enter your Anthropic API key: " api_key
    echo "ANTHROPIC_API_KEY=$api_key" > .env
    echo ".env file created."
fi

echo ""
echo "Starting services..."

# Start FastAPI in background
echo "Starting API server on port $API_PORT..."
uvicorn src.contract_simulator.api.main:app --host 0.0.0.0 --port $API_PORT &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API to start..."
for i in $(seq 1 30); do
    if curl -s "http://localhost:$API_PORT/health" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Start Streamlit
echo "Starting frontend on port $FRONTEND_PORT..."
streamlit run frontend/app.py --server.port $FRONTEND_PORT --server.headless true &
FRONTEND_PID=$!

# Wait a moment then open browser
sleep 2
if command -v open &> /dev/null; then
    open "http://localhost:$FRONTEND_PORT"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:$FRONTEND_PORT"
fi

echo ""
echo "========================================="
echo "  Contract Simulator is running!"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "  API Docs: http://localhost:$API_PORT/docs"
echo "  Press Ctrl+C to stop"
echo "========================================="

# Clean shutdown on Ctrl+C
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $FRONTEND_PID 2>/dev/null || true
    kill $API_PID 2>/dev/null || true
    wait $FRONTEND_PID 2>/dev/null || true
    wait $API_PID 2>/dev/null || true
    echo "Stopped."
}
trap cleanup INT TERM

# Wait for processes
wait
