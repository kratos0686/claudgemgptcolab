@echo off
title AI Collaboration Tool
setlocal EnableDelayedExpansion

echo ──────────────────────────────────────────────────────────────
echo   AI Collaboration Tool
echo ──────────────────────────────────────────────────────────────
echo.

:: ── Load .env if present ─────────────────────────────────────────────────────
if exist "%~dp0.env" (
    echo   Loading API keys from .env file...
    for /f "usebackq tokens=1,* delims==" %%A in ("%~dp0.env") do (
        set line=%%A
        if not "!line:~0,1!"=="#" (
            if not "%%B"=="" set "%%A=%%B"
        )
    )
)

:: ── Check required API keys ───────────────────────────────────────────────────
set MISSING=0

if "%ANTHROPIC_API_KEY%"=="" (
    echo   ERROR: ANTHROPIC_API_KEY is not set.
    set MISSING=1
)
if "%OPENAI_API_KEY%"=="" (
    echo   ERROR: OPENAI_API_KEY is not set.
    set MISSING=1
)
if "%GEMINI_API_KEY%"=="" (
    echo   ERROR: GEMINI_API_KEY is not set.
    set MISSING=1
)

if "%MISSING%"=="1" (
    echo.
    echo   Option 1 -- create a .env file ^(recommended^):
    echo     copy .env.example .env
    echo     ^(then edit .env and paste your keys^)
    echo.
    echo   Option 2 -- set system environment variables:
    echo     Start ^> "Edit system environment variables" ^> Environment Variables
    echo.
    pause
    exit /b 1
)

echo   API keys: OK  ANTHROPIC  OPENAI  GEMINI
echo.

:: ── Install/upgrade dependencies ─────────────────────────────────────────────
echo   Checking dependencies...
python -c "import anthropic, openai, dotenv; from google import genai" >nul 2>&1
if errorlevel 1 (
    echo   Installing dependencies...
    pip install -q -r "%~dp0requirements.txt"
    echo   Dependencies installed.
) else (
    echo   Dependencies: already installed.
)
echo.

:: ── Launch ────────────────────────────────────────────────────────────────────
python "%~dp0ai_collaboration.py"

echo.
pause
