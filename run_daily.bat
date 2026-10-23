@echo off
rem The daily run.
rem   run_daily.bat         fetch + triage (skipped if already done today), then Claude does /daily-run
rem   run_daily.bat fetch   fetch + triage only, no window prompts (used by the scheduled task)
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
  echo Run setup.bat first.
  pause
  exit /b 1
)
if /i "%~1"=="fetch" goto fetch_only

echo === 1/2  Fetch new jobs + triage  (20-40 min unless already done today) ===
".venv\Scripts\python.exe" -m jobsearch daily
if errorlevel 1 (
  echo Fetch or triage failed - see data\logs\ for details.
  pause
  exit /b 1
)

echo.
echo === 2/2  Choosing jobs and writing cover letters in Claude ===
set "CLAUDE_EXE="
where claude >nul 2>nul
if not errorlevel 1 set "CLAUDE_EXE=claude"
if not defined CLAUDE_EXE if exist "%USERPROFILE%\.local\bin\claude.exe" set "CLAUDE_EXE=%USERPROFILE%\.local\bin\claude.exe"
if defined CLAUDE_EXE (
  call "%CLAUDE_EXE%" "/daily-run"
  if exist "output\Job Tracker.xlsx" start "" "output\Job Tracker.xlsx"
) else (
  echo The Claude Code command line was not found.
  echo Open this folder in the Claude desktop app ^(Code tab^) and type:   /daily-run
)
pause
exit /b 0

:fetch_only
if not exist "data\logs" mkdir "data\logs"
".venv\Scripts\python.exe" -m jobsearch daily >> "data\logs\scheduled.log" 2>&1
exit /b %errorlevel%
