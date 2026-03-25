@echo off
title AI Collaboration Tool

:: ── Check API keys are set in system environment variables ──────────────────
if "%ANTHROPIC_API_KEY%"=="" (
    echo ERROR: ANTHROPIC_API_KEY is not set.
    echo.
    echo Set it via: Start ^> "Edit system environment variables" ^> Environment Variables
    echo Then restart this Command Prompt window.
    pause
    exit /b 1
)
if "%OPENAI_API_KEY%"=="" (
    echo ERROR: OPENAI_API_KEY is not set.
    echo.
    echo Set it via: Start ^> "Edit system environment variables" ^> Environment Variables
    echo Then restart this Command Prompt window.
    pause
    exit /b 1
)
if "%GEMINI_API_KEY%"=="" (
    echo ERROR: GEMINI_API_KEY is not set.
    echo.
    echo Set it via: Start ^> "Edit system environment variables" ^> Environment Variables
    echo Then restart this Command Prompt window.
    pause
    exit /b 1
)

:: ── Install dependencies (only needed once) ────────────────────────────────
pip show anthropic >nul 2>&1 || pip install anthropic>=0.40.0 google-genai>=0.8.0 openai>=1.0.0

:: ── Launch ──────────────────────────────────────────────────────────────────
python "%~dp0ai_collaboration.py"

pause
