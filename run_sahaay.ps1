# eSahaay One-Click PowerShell Launcher
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $scriptDir

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "Starting eSahaay - Emergency Response & Triage System" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

Write-Host "`n[1/2] Seeding demo database..." -ForegroundColor Yellow
python "$scriptDir\scripts\seed_demo.py"

Write-Host "`n[2/2] Launching eSahaay Streamlit Application on http://localhost:8501 ..." -ForegroundColor Green
python -m streamlit run "$scriptDir\app.py" --server.port=8501
