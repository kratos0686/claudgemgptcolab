@echo off
setlocal EnableDelayedExpansion
title AI Collaboration Tool - Portable Setup

set "DIR=%~dp0"
set "PYDIR=%DIR%.python"
set "PYVER=3.12.9"
set "PYZIP=python-%PYVER%-embed-amd64.zip"
set "PYURL=https://www.python.org/ftp/python/%PYVER%/%PYZIP%"
set "PIPURL=https://bootstrap.pypa.io/get-pip.py"

echo.
echo ================================================================
echo   AI Collaboration Tool -- Portable USB Setup (Windows)
echo ================================================================
echo.
echo  This will download Python %PYVER% and all dependencies
echo  directly onto this drive. No system install required.
echo.

if exist "%PYDIR%\python.exe" (
    echo  Python already present at .python\  -- skipping download.
    goto :deps
)

:: ── Download Python embeddable ───────────────────────────────────────────────
echo  [1/4] Downloading Python %PYVER% embeddable ...
powershell -NoProfile -Command ^
  "Invoke-WebRequest -Uri '%PYURL%' -OutFile '%DIR%%PYZIP%'" ^
  2>nul
if not exist "%DIR%%PYZIP%" (
    echo.
    echo  ERROR: Download failed. Check your internet connection.
    pause & exit /b 1
)

:: ── Extract ──────────────────────────────────────────────────────────────────
echo  [2/4] Extracting ...
powershell -NoProfile -Command ^
  "Expand-Archive -Path '%DIR%%PYZIP%' -DestinationPath '%PYDIR%' -Force"
del "%DIR%%PYZIP%"

:: ── Enable site-packages (required for pip to work in embeddable) ────────────
echo  [3/4] Enabling site-packages ...
for %%F in ("%PYDIR%\python3*._pth") do (
    powershell -NoProfile -Command ^
      "(Get-Content '%%F') -replace '#import site','import site' | Set-Content '%%F'"
)

:: ── Install pip ──────────────────────────────────────────────────────────────
echo  [4/4] Installing pip ...
powershell -NoProfile -Command ^
  "Invoke-WebRequest -Uri '%PIPURL%' -OutFile '%PYDIR%\get-pip.py'"
"%PYDIR%\python.exe" "%PYDIR%\get-pip.py" --no-warn-script-location -q
del "%PYDIR%\get-pip.py"

:deps
:: ── Install / update dependencies ───────────────────────────────────────────
echo.
echo  Installing dependencies into portable Python ...
"%PYDIR%\python.exe" -m pip install -q --no-warn-script-location ^
    anthropic>=0.40.0 google-genai>=0.8.0 openai>=1.0.0 python-dotenv>=1.0.0 pyinstaller>=6.0.0

echo.
echo ================================================================
echo   Setup complete!
echo   Run the tool with:  run.bat
echo ================================================================
echo.
pause
