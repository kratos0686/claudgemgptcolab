@echo off
setlocal enabledelayedexpansion
title AI Collaboration Tool - Setup

echo ============================================
echo  AI Collaboration Tool - Portable Setup
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Downloading and installing Python 3.11...
    echo.
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    del "%TEMP%\python_installer.exe"
    echo Python installed. Please restart this script.
    pause
    exit /b 0
)

echo Python found:
python --version
echo.

REM Create local venv if it doesn't exist
if not exist ".venv" (
    echo Creating local virtual environment...
    python -m venv .venv
    echo Done.
    echo.
)

REM Activate venv and install dependencies
echo Installing dependencies into local .venv...
call .venv\Scripts\activate.bat
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo Done.
echo.

REM Check for .env file
if exist ".env" (
    echo Found .env file - API keys will be loaded automatically.
) else (
    echo No .env file found. Copying .env.example to .env...
    copy .env.example .env >nul
    echo.
    echo IMPORTANT: Open .env and fill in your API keys before running the tool.
    echo   - ANTHROPIC_API_KEY
    echo   - OPENAI_API_KEY
    echo   - GEMINI_API_KEY
)

echo.
echo ============================================
echo  Setup complete!
echo  Run 'run_portable.bat' to start the tool.
echo ============================================
echo.
pause
