@echo off
rem Optional: fetch new jobs automatically every day at 18:15, so that run_daily.bat in the
rem evening goes straight to Claude.
rem   schedule_fetch.bat          create / update the task
rem   schedule_fetch.bat remove   delete the task
setlocal
set "TASK=Daily Job Search Fetch"
if /i "%~1"=="remove" (
  schtasks /Delete /F /TN "%TASK%"
  pause
  exit /b %errorlevel%
)
schtasks /Create /F /TN "%TASK%" /SC DAILY /ST 18:15 /TR "\"%~dp0run_daily.bat\" fetch"
if errorlevel 1 (
  echo Could not create the task.
) else (
  echo Task "%TASK%" runs every day at 18:15 while you are logged in.
  echo Change the time in Windows Task Scheduler, or run: schedule_fetch.bat remove
)
pause
