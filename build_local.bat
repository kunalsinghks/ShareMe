@echo off
setlocal
cd /d "%~dp0"
echo [*] Cleaning previous builds...
rd /s /q dist build 2>nul
echo [*] Building ShareME.exe...
pyinstaller ShareME.spec
if %errorlevel% neq 0 (
    echo [X] Build Failed!
    pause
    exit /b 1
)
echo [!] IMPORTANT: The built app is in dist/ShareME/
echo [!] Please navigate to dist/ShareME/ and run ShareME.exe to test.
pause
