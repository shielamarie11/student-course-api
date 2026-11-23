@echo off
title Campus Connect - Flask Backend
cd /d "%~dp0"

if not exist venv (
  echo No virtual environment found. Run run.bat first.
  pause
  exit /b 1
)

call venv\Scripts\activate
echo Starting the Campus Connect API at http://127.0.0.1:5000/api
python app.py
pause