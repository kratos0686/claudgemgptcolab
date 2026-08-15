@echo off
setlocal enabledelayedexpansion
title AI Collaboration Tool - Setup

REM ── AI Collaboration Tool — Setup ──────────────────────────────────────────
REM Creates a virtual environment, installs dependencies, and configures
REM API keys so the tool is ready to run.
REM
REM Usage:
REM   setup.bat              Setup only
REM   setup.bat --run        Setup then launch the CLI tool
REM   setup.bat --run-server Setup then launch the GUI server

cd /d "%~dp0"

set "RUN_AFTER="
if "%~1"=="--run" set "RUN_AFTER=cli"
if "%~1"=="--run-server" set "RUN_AFTER=server"
if "%~1"=="--help" goto :usage
if "%~1"=="-h" goto :usage

echo.
echo   ======================================
echo    AI Collaboration Tool - Setup
echo   ======================================
echo.

REM ── 1. Check Python ──────────────────────────────────────────────────────
echo [Step 1/4] Checking Python installation...

REM Prefer embedded .python if available (portable/USB install)
set "PYTHON_CMD="
if exist ".python\python.exe" (
    set "PYTHON_CMD=.python\python.exe"
    goto :python_found
)

REM Try system python
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :python_found
)

python3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python3"
    goto :python_found
)

echo   ERROR: Python 3.9+ is required but not found.
echo.
echo   Install Python from: https://www.python.org/downloads/
echo   Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:python_found
for /f "tokens=*" %%v in ('!PYTHON_CMD! --version 2^>^&1') do set "PY_VER=%%v"
echo   Found: !PY_VER!
echo.

REM ── 2. Create virtual environment ────────────────────────────────────────
echo [Step 2/4] Setting up virtual environment...

if exist ".venv\Scripts\activate.bat" (
    echo   Virtual environment already exists at .venv\
) else (
    !PYTHON_CMD! -m venv .venv
    if errorlevel 1 (
        echo   ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo   Created virtual environment at .venv\
)
echo.

REM Activate
call .venv\Scripts\activate.bat

REM ── 3. Install dependencies ──────────────────────────────────────────────
echo [Step 3/4] Installing dependencies...

pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo   ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo   All dependencies installed.
echo.

REM ── 4. Configure API keys ───────────────────────────────────────────────
echo [Step 4/4] Checking API key configuration...

REM Load .env if it exists
if exist ".env" (
    echo   Found .env file.
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "LINE=%%a"
        if not "!LINE:~0,1!"=="#" (
            if not "!LINE!"=="" (
                REM Strip leading "export "
                set "CLEAN=!LINE!"
                if "!CLEAN:~0,7!"=="export " set "CLEAN=!CLEAN:~7!"
                set "!CLEAN!=%%b"
            )
        )
    )
) else if exist ".env.example" (
    copy .env.example .env >nul
    echo   Created .env from .env.example -- you need to fill in your API keys.
) else (
    echo   No .env file found. Set API keys as environment variables.
)

REM Check each key
set "MISSING=0"
set "MISSING_LIST="

if not defined ANTHROPIC_API_KEY (
    set /a MISSING+=1
    set "MISSING_LIST=!MISSING_LIST! ANTHROPIC_API_KEY"
)
if not defined OPENAI_API_KEY (
    set /a MISSING+=1
    set "MISSING_LIST=!MISSING_LIST! OPENAI_API_KEY"
)
if not defined GEMINI_API_KEY (
    set /a MISSING+=1
    set "MISSING_LIST=!MISSING_LIST! GEMINI_API_KEY"
)

if !MISSING! equ 0 (
    echo   All API keys are configured.
) else (
    echo   Missing or placeholder API keys:
    for %%k in (!MISSING_LIST!) do echo     - %%k
    echo.
    echo   Edit .env and fill in your real keys:
    echo     ANTHROPIC_API_KEY  -- https://console.anthropic.com
    echo     OPENAI_API_KEY     -- https://platform.openai.com/api-keys
    echo     GEMINI_API_KEY     -- https://aistudio.google.com/app/apikey
)

echo.

REM ── Summary ─────────────────────────────────────────────────────────────
echo   ======================================
echo    Setup complete!
echo   ======================================
echo.
echo   To run the CLI collaboration tool:
echo     .venv\Scripts\activate.bat
echo     python ai_collaboration.py
echo.
echo   To run the GUI web server:
echo     .venv\Scripts\activate.bat
echo     python server.py
echo.
echo   To run the autonomous code agent:
echo     .venv\Scripts\activate.bat
echo     python launch_agent.py
echo.

REM ── Optional: auto-launch ───────────────────────────────────────────────
if "!RUN_AFTER!"=="cli" (
    echo Launching CLI collaboration tool...
    echo.
    python ai_collaboration.py
)
if "!RUN_AFTER!"=="server" (
    echo Launching GUI server...
    echo.
    python server.py
)

pause
exit /b 0

:usage
echo Usage: setup.bat [--run ^| --run-server]
echo   --run          Setup then launch the CLI collaboration tool
echo   --run-server   Setup then launch the GUI web server
exit /b 0
