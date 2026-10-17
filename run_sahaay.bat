@echo off
title eSahaay - Emergency Response & Triage System
echo ====================================================================
echo Starting eSahaay - Emergency Response & Triage System
echo ====================================================================

:: Navigate to this script's directory
cd /d "%~dp0"

echo [1/2] Seeding demo database...
python scripts\seed_demo.py

echo.
echo [2/2] Launching eSahaay Streamlit Application on http://localhost:8501 ...
python -m streamlit run app.py --server.port=8501

pause
