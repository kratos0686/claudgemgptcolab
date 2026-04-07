@echo off
setlocal EnableDelayedExpansion
title AI Collaboration Tool - Portable Setup

set "DIR=%~dp0"
set "VENV=%DIR%.venv"
set "PYVER=3.12.9"
set "PYURL=https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-amd64.exe"
set "PYINST=%DIR%python_installer.exe"

echo.
echo ================================================================
echo   AI Collaboration Tool -- Portable Setup (Windows)
echo ================================================================
echo.

:: ── Check for Python ─────────────────────────────────────────────────────────
set "PYTHON="
for %%C in (python python3) do (
    if "!PYTHON!"=="" (
        %%C --version >nul 2>&1 && set "PYTHON=%%C"
    )
)

if "!PYTHON!"=="" (
    echo  Python not found. Downloading Python %PYVER% installer...
    powershell -NoProfile -Command ^
      "Invoke-WebRequest -Uri '%PYURL%' -OutFile '%PYINST%'" 2>nul
    if not exist "%PYINST%" (
        echo  ERROR: Download failed. Check your internet connection.
        pause & exit /b 1
    )
    echo  Installing Python %PYVER% silently (user scope, no admin needed)...
    "%PYINST%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    del "%PYINST%"
    :: Refresh PATH so python is visible
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
    set "PYTHON=python"
) else (
    echo  Found Python: & %PYTHON% --version
)

:: ── Create local .venv ───────────────────────────────────────────────────────
if not exist "%VENV%\Scripts\activate.bat" (
    echo.
    echo  Creating local .venv in project folder...
    %PYTHON% -m venv "%VENV%"
    if errorlevel 1 (
        echo  ERROR: Failed to create virtual environment.
        pause & exit /b 1
    )
)

:: ── Install dependencies ─────────────────────────────────────────────────────
echo.
echo  Installing dependencies into .venv...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip -q
"%VENV%\Scripts\pip.exe" install -q -r "%DIR%requirements.txt"
if errorlevel 1 (
    echo  ERROR: pip install failed.
    pause & exit /b 1
)

:: ── Load .env if present ─────────────────────────────────────────────────────
if exist "%DIR%.env" (
    echo.
    echo  Loading API keys from .env...
    for /f "usebackq tokens=1,* delims==" %%A in ("%DIR%.env") do (
        set "line=%%A"
        if not "!line:~0,1!"=="#" if not "!line!"=="" (
            set "%%A=%%B"
        )
    )
    echo  Done.
) else (
    echo.
    echo  No .env file found. Copy .env.example to .env and add your API keys.
)

echo.
echo ================================================================
echo   Setup complete!
echo   Run the tool with:  run_portable.bat
echo ================================================================
echo.
pause
