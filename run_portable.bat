@echo off
setlocal enabledelayedexpansion
title AI Collaboration Tool

REM Check venv exists
if not exist ".venv" (
    echo Setup not complete. Please run setup_portable.bat first.
    pause
    exit /b 1
)

REM Check .env exists
if not exist ".env" (
    echo No .env file found. Please copy .env.example to .env and fill in your API keys.
    pause
    exit /b 1
)

REM Activate venv and run
call .venv\Scripts\activate.bat
python ai_collaboration.py
pause
