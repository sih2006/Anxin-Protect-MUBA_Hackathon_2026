# Anxin -- Windows backend setup + run.
#
#   Right-click > Run with PowerShell, or from a terminal:
#       powershell -ExecutionPolicy Bypass -File .\setup-backend.ps1
#
# Creates the virtualenv, installs dependencies, makes sure backend\.env
# exists, then starts the API on http://localhost:8000

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot\backend

Write-Host "==> Checking Python..." -ForegroundColor Cyan
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) {
    Write-Host "Python not found. Install Python 3.11+ from https://python.org and re-run." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "==> Creating virtual environment..." -ForegroundColor Cyan
    & $python.Source -m venv .venv
}

# A venv created from Git Bash by an MSYS/MinGW Python uses the POSIX layout
# (.venv\bin) rather than the Windows one (.venv\Scripts). Mixing shells on the
# same folder is an easy way to end up with one and be looking for the other,
# so resolve whichever is actually there instead of assuming.
$venvPython = $null
if (Test-Path ".venv\Scripts\python.exe")  { $venvPython = ".\.venv\Scripts\python.exe" }
elseif (Test-Path ".venv\bin\python.exe")  { $venvPython = ".\.venv\bin\python.exe" }
elseif (Test-Path ".venv\bin\python")      { $venvPython = ".\.venv\bin\python" }

if (-not $venvPython) {
    Write-Host ""
    Write-Host "ERROR: backend\.venv exists but has no usable Python interpreter." -ForegroundColor Red
    Write-Host "       It was probably created by a different shell (Git Bash vs PowerShell)." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Fix it either way:" -ForegroundColor Yellow
    Write-Host "    - Rebuild for PowerShell:  rmdir /s /q backend\.venv   then re-run this script" -ForegroundColor Yellow
    Write-Host "    - Or stay in Git Bash:     ./setup.sh backend" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "==> Installing dependencies (first run takes a minute)..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r requirements.txt --quiet

if (-not (Test-Path ".env")) {
    Write-Host "==> No .env found -- creating one from .env.example." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "  IMPORTANT: open backend\.env and set:" -ForegroundColor Yellow
    Write-Host "     GONKA_API_KEY=<your key>" -ForegroundColor Yellow
    Write-Host "     GONKA_MOCK_MODE=false" -ForegroundColor Yellow
    Write-Host ""
}

$envText = Get-Content ".env" -Raw
if ($envText -match "GONKA_API_KEY=sk-REPLACE_ME") {
    Write-Host "WARNING: backend\.env still has the placeholder API key." -ForegroundColor Yellow
    Write-Host "         The app will run, but only with mock data." -ForegroundColor Yellow
}
if ($envText -match "GONKA_MOCK_MODE=true") {
    Write-Host "NOTE: GONKA_MOCK_MODE=true -- results will be clearly-labelled MOCK data," -ForegroundColor Yellow
    Write-Host "      not real Gonka inference. Set it to false for the live demo." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==> Starting Anxin API on http://localhost:8000  (Ctrl+C to stop)" -ForegroundColor Green
Write-Host "    Health check: http://localhost:8000/health" -ForegroundColor Green
Write-Host "    API docs:     http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
& $venvPython -m uvicorn app.main:app --reload --port 8000
