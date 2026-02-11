@echo off
setlocal
cd /d "%~dp0"
title ShareME DEBUG MODE
echo [*] Killing existing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /C:":8000 "') do (
    if not "%%a"=="" taskkill /F /PID %%a >nul 2>&1
)
echo [*] Starting ShareME in DEBUG mode (Visible Console)...
python gui.py
pause
