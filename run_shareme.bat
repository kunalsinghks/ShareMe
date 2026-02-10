@echo off
setlocal
cd /d "%~dp0"
title ShareME Background Engine

:: Kill existing process on port 8000 to prevent startup errors
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /C:":8000 "') do (
    if not "%%a"=="" (
        taskkill /F /PID %%a >nul 2>&1
    )
)

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Error: Python is not installed.
    pause
    exit /b 1
)

:: Launching via pythonw.exe hides the black console window
echo [*] Launching ShareME in Background Mode...
start "" pythonw gui.py
exit
