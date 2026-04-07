@echo off
setlocal EnableDelayedExpansion
title AI Collaboration Tool

set "DIR=%~dp0"
set "EMBEDDED=%DIR%.python\python.exe"
set "VENV=%DIR%.venv\Scripts\python.exe"

echo.
echo ================================================================
echo   AI Collaboration Tool
echo ================================================================
echo.

:: ── Load .env if present ─────────────────────────────────────────────────────
if exist "%DIR%.env" (
    echo   Loading API keys from .env ...
    for /f "usebackq tokens=1,* delims==" %%A in ("%DIR%.env") do (
        set "line=%%A"
        if not "!line:~0,1!"=="#" if not "%%B"=="" set "%%A=%%B"
    )
)

:: ── Check API keys ───────────────────────────────────────────────────────────
set MISSING=0
if "%ANTHROPIC_API_KEY%"=="" set MISSING=1
if "%OPENAI_API_KEY%"==""    set MISSING=1
if "%GEMINI_API_KEY%"==""    set MISSING=1

if "%MISSING%"=="1" (
    echo   ERROR: One or more API keys are missing.
    echo.
    echo   Create a .env file with your keys ^(recommended^):
    echo     1. Copy .env.example to .env
    echo     2. Open .env and paste your keys
    echo.
    echo   Or set them as Windows environment variables:
    echo     Start ^> "Edit system environment variables" ^> Environment Variables
    echo.
    pause & exit /b 1
)

echo   API keys: OK
echo.

:: ── Pick Python runtime ──────────────────────────────────────────────────────

:: 1) Prefer embedded Python bundled by setup_portable.bat
if exist "%EMBEDDED%" (
    echo   Using bundled Python at .python\
    set "PY=%EMBEDDED%"
    goto :install_deps
)

:: 2) Fall back to system Python + local venv
where python >nul 2>&1
if not errorlevel 1 (
    if not exist "%VENV%" (
        echo   Creating local virtual environment at .venv\ ...
        python -m venv "%DIR%.venv"
    )
    set "PY=%VENV%"
    goto :install_deps
)

:: 3) No Python at all — offer to run first-time setup
echo   Python not found on this system.
echo.
echo   Run setup_portable.bat first to download a bundled Python runtime:
echo     Double-click setup_portable.bat   ^(needs internet, ~30 MB, one-time^)
echo.
echo   Then run this script again.
echo.
pause & exit /b 1

:install_deps
:: ── Install / verify dependencies ────────────────────────────────────────────
"%PY%" -c "import anthropic, openai, dotenv; from google import genai" >nul 2>&1
if errorlevel 1 (
    echo   Installing dependencies ...
    "%PY%" -m pip install -q -r "%DIR%requirements.txt"
    echo   Dependencies installed.
) else (
    echo   Dependencies: OK
)
echo.

:run
"%PY%" "%DIR%ai_collaboration.py"

echo.
pause
