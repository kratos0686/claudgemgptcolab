@echo off
setlocal EnableDelayedExpansion
title AI Collaboration Tool

set "DIR=%~dp0"
set "VENV=%DIR%.venv"

if not exist "%VENV%\Scripts\activate.bat" (
    echo  .venv not found. Please run setup_portable.bat first.
    pause & exit /b 1
)

:: Load .env if present
if exist "%DIR%.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%DIR%.env") do (
        set "line=%%A"
        if not "!line:~0,1!"=="#" if not "!line!"=="" (
            set "%%A=%%B"
        )
    )
)

call "%VENV%\Scripts\activate.bat"
python "%DIR%ai_collaboration.py"
