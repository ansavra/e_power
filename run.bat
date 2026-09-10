@echo off
setlocal
title E-POWER - Electricity Billing System
cd /d "%~dp0"

echo ===============================================================
echo   E-POWER: ELECTRICITY BILLING SYSTEM (WEB APPLICATION)
echo   Starting server at http://127.0.0.1:5050 ...
echo ===============================================================
echo.

:: Automatically open default web browser after server starts
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:5050"

:: Start the Python Web Application
python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Server exited or failed to start.
    pause
)
