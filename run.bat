@echo off
setlocal EnableDelayedExpansion
title AI Collaboration Tool

set "DIR=%~dp0"
set "EMBEDDED=%DIR%.python\python.exe"
set "VENV=%DIR%.venv\Scripts\python.exe"

:: ── Check API keys ───────────────────────────────────────────────────────────
if "%ANTHROPIC_API_KEY%"=="" (
    echo ERROR: ANTHROPIC_API_KEY is not set.
    echo.
    echo Set it via: Start ^> "Edit system environment variables" ^> Environment Variables
    echo Then restart this window and try again.
    pause & exit /b 1
)
if "%OPENAI_API_KEY%"=="" (
    echo ERROR: OPENAI_API_KEY is not set.
    echo.
    echo Set it via: Start ^> "Edit system environment variables" ^> Environment Variables
    echo Then restart this window and try again.
    pause & exit /b 1
)
if "%GEMINI_API_KEY%"=="" (
    echo ERROR: GEMINI_API_KEY is not set.
    echo.
    echo Set it via: Start ^> "Edit system environment variables" ^> Environment Variables
    echo Then restart this window and try again.
    pause & exit /b 1
)

:: ── Pick Python runtime ──────────────────────────────────────────────────────
if exist "%EMBEDDED%" (
    echo  Using portable Python (.python\)
    set "PY=%EMBEDDED%"
    goto :run
)

:: Fall back to system Python + local venv
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo.
    echo Option A -- Run setup_portable.bat to install Python onto this drive.
    echo Option B -- Install Python from https://python.org and re-run.
    pause & exit /b 1
)

if not exist "%VENV%" (
    echo  Creating local virtual environment ...
    python -m venv "%DIR%.venv"
)
set "PY=%VENV%"

:: ── Install / verify dependencies ───────────────────────────────────────────
echo  Checking dependencies ...
"%PY%" -m pip show anthropic >nul 2>&1 && ^
"%PY%" -m pip show openai    >nul 2>&1 && ^
"%PY%" -m pip show google-genai >nul 2>&1 || ^
"%PY%" -m pip install -q anthropic>=0.40.0 google-genai>=0.8.0 openai>=1.0.0

:run
"%PY%" "%DIR%ai_collaboration.py"
pause
