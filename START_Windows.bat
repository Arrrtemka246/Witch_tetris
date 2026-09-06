@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe goto ready
where py >nul 2>nul
if errorlevel 1 (
  python -m venv .venv
) else (
  py -3 -m venv .venv
)
if not exist .venv\Scripts\python.exe (
  echo Install Python 3.12 from python.org, then run again.
  pause
  exit /b 1
)
:ready
.venv\Scripts\python.exe -c "import pygame" >nul 2>nul
if errorlevel 1 (
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (
    pause
    exit /b 1
  )
)
.venv\Scripts\python.exe playtest.py
pause
