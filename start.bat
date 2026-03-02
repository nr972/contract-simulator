@echo off
REM Contract Simulator — One-command launcher (Windows)
REM Usage: start.bat

set API_PORT=8000
set FRONTEND_PORT=8501

echo =========================================
echo   Contract Simulator ^& Stress-Tester
echo =========================================

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3 is required but not found.
    echo Install Python from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment if needed
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Install dependencies if needed
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies ^(first run only^)...
    pip install -q .
)

REM Check for .env file
if not exist ".env" (
    echo.
    echo No .env file found.
    echo You need an Anthropic API key to use this tool.
    echo Get one at: https://console.anthropic.com/
    echo.
    set /p api_key="Enter your Anthropic API key: "
    echo ANTHROPIC_API_KEY=%api_key%> .env
    echo .env file created.
)

echo.
echo Starting services...

REM Start FastAPI in background
echo Starting API server on port %API_PORT%...
start /b uvicorn src.contract_simulator.api.main:app --host 0.0.0.0 --port %API_PORT%

REM Wait for API
echo Waiting for API to start...
timeout /t 5 /nobreak >nul

REM Start Streamlit
echo Starting frontend on port %FRONTEND_PORT%...
start /b streamlit run frontend/app.py --server.port %FRONTEND_PORT% --server.headless true

REM Wait then open browser
timeout /t 3 /nobreak >nul
start http://localhost:%FRONTEND_PORT%

echo.
echo =========================================
echo   Contract Simulator is running!
echo   Frontend: http://localhost:%FRONTEND_PORT%
echo   API Docs: http://localhost:%API_PORT%/docs
echo   Press Ctrl+C to stop
echo =========================================

REM Keep window open
pause
