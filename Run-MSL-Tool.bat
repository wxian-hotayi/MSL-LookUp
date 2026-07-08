@echo off
title MSL Lookup Tool
cd /d "%~dp0msl_lookup"

set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)

if not defined PY (
    echo [ERROR] Python 3 is not installed or not on PATH.
    echo Install it from https://www.python.org/downloads/ ^(tick "Add Python to PATH"^).
    pause
    exit /b 1
)

echo Checking dependencies...
%PY% -c "import flask, pandas, openpyxl, requests" 2>nul
if errorlevel 1 (
    echo Installing required packages ^(first run only^)...
    %PY% -m pip install -r requirements.txt || (echo [ERROR] Install failed. & pause & exit /b 1)
)

echo.
echo Starting MSL Lookup Tool - your browser will open at http://localhost:5000
echo Keep this window open while using the tool. Close it to stop the server.
echo.
%PY% app.py
pause
