@echo off
setlocal
cd /d "%~dp0"
title ShareME Debug Launcher

echo ==========================================
echo    ShareME - Debug Mode
echo ==========================================
echo.

echo [*] Testing Python...
python --version
if %errorlevel% neq 0 (
    echo [X] Python check failed.
)

echo.
echo [*] Starting main.py...
python main.py

echo.
echo ==========================================
echo Server process finished.
echo Exit Code: %errorlevel%
pause
