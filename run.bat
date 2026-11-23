@echo off
title Campus Connect - Flask Backend
cd /d "%~dp0"

echo ============================================
echo   Campus Connect - Integrated SIS Backend
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10+ from https://python.org
  echo and tick "Add Python to PATH" during setup.
  pause
  exit /b 1
)

if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
)

call venv\Scripts\activate

echo Installing requirements...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt

echo.
echo Starting the API at http://127.0.0.1:5000/api
echo Press CTRL+C to stop the server.
echo.
python app.py

pause