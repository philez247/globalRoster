# PowerShell script to start the Global Roster server
# Usage: .\start_server.ps1

# Navigate to project directory
Set-Location $PSScriptRoot

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

# Start the server
Write-Host "Starting FastAPI server on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
uvicorn global_roster.main:app --reload --port 8000



