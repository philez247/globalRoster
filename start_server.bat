@echo off
REM Batch script to start the Global Roster server
REM Usage: start_server.bat

REM Navigate to project directory
cd /d "%~dp0"

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Start the server
echo Starting FastAPI server on http://127.0.0.1:8000
echo Press Ctrl+C to stop the server
uvicorn global_roster.main:app --reload --port 8000

pause



