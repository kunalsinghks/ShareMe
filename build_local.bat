@echo off
setlocal
cd /d "%~dp0"
echo [*] Cleaning previous builds...
rd /s /q dist build 2>nul
echo [*] Building ShareME.exe (v1.5.5)...
pyinstaller ShareME.spec
if %errorlevel% neq 0 (
    echo [X] Build Failed!
    pause
    exit /b 1
)
echo [!] SUCCESS: The built app is in dist/ShareME/
pause
