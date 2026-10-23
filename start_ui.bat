@echo off
rem Opens the control panel (Start/Stop button + last run time) in your browser.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" ui.py
pause
