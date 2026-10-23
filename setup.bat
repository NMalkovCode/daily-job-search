@echo off
rem One-time setup: creates .venv, installs the packages, creates your config files, checks everything.
setlocal
cd /d "%~dp0"
echo === Daily Job Search - setup ===

set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
  where python >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if not defined PY (
  echo Python was not found. Install Python 3.10 or newer from https://www.python.org/downloads/
  echo ^(tick "Add python.exe to PATH"^), then run setup.bat again.
  pause
  exit /b 1
)

rem a .venv copied from another PC does not work here - recreate it
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
  if errorlevel 1 (
    echo The existing .venv does not work on this PC - recreating it ...
    rmdir /s /q ".venv"
  )
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating the virtual environment .venv ...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo Could not create .venv
    pause
    exit /b 1
  )
)

echo Installing packages ...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q --upgrade pip
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
  echo Package installation failed - check the internet connection and run setup.bat again.
  pause
  exit /b 1
)

rem Your own copies of the example files. They are git-ignored, so your details stay private.
call :make_config settings.example.json settings.json
call :make_config secrets.example.json secrets.json
call :make_config companies.example.json companies.json
call :make_config profile.example.md profile.md

echo.
".venv\Scripts\python.exe" -m jobsearch doctor
echo.
echo Setup finished. Next:
echo  1. Fill in config\profile.md and the "candidate" part of config\settings.json
echo     (or open this folder in Claude Code and ask it to help - see README.md).
echo  2. Copy your CV files into the "cvs" folder (see cvs\README.md).
echo  3. Optional: add free API keys to config\secrets.json (see docs\sources.md).
echo  4. Every day: double-click run_daily.bat (or start_ui.bat for a Start/Stop panel).
pause
exit /b 0

:make_config
if not exist "config\%~2" (
  copy "config\%~1" "config\%~2" >nul
  echo Created config\%~2 from config\%~1 - fill it in.
)
exit /b 0
