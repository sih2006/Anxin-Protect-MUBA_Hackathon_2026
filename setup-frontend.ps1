# Anxin -- Windows frontend setup + run.
#
#   powershell -ExecutionPolicy Bypass -File .\setup-frontend.ps1
#
# Installs npm dependencies, ensures .env.local points at the local API,
# then starts the web app on http://localhost:3000
#
# Run setup-backend.ps1 in a SEPARATE terminal first -- both need to be
# running at the same time.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot\frontend

Write-Host "==> Checking Node..." -ForegroundColor Cyan
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js not found. Install Node 18+ from https://nodejs.org and re-run." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "node_modules")) {
    Write-Host "==> Installing dependencies (first run takes a few minutes)..." -ForegroundColor Cyan
    npm install
}

if (-not (Test-Path ".env.local")) {
    Write-Host "==> Creating .env.local pointing at http://localhost:8000" -ForegroundColor Cyan
    Copy-Item ".env.example" ".env.local"
}

Write-Host ""
Write-Host "==> Starting Anxin web app on http://localhost:3000  (Ctrl+C to stop)" -ForegroundColor Green
Write-Host ""
npm run dev
