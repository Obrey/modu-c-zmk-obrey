@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 scripts\apply_to_repo.py
) else (
    python scripts\apply_to_repo.py
)
set "result=%errorlevel%"
echo.
if not "%result%"=="0" echo Installation stopped. Read the message above. Do not push partial changes.
pause
exit /b %result%
