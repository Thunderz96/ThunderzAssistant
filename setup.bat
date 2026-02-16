@echo off
title Thunderz Assistant - Setup
echo.
echo  =============================================
echo   ⚡  Thunderz Assistant  -  First-Time Setup
echo  =============================================
echo.

REM ── 1. Check Python is available ──────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not on PATH.
    echo  Download Python 3.9+ from https://www.python.org/downloads/
    echo  Make sure to tick "Add Python to PATH" during install.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  Found: %PYVER%
echo.

REM ── 2. Create virtual environment ─────────────────────────────────────────
if exist ".venv\" (
    echo  [SKIP] Virtual environment already exists (.venv\)
) else (
    echo  [1/5] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo        Done.
)
echo.

REM ── 3. Install dependencies ────────────────────────────────────────────────
echo  [2/5] Installing dependencies from requirements.txt...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\pip.exe install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] pip install failed. Check requirements.txt and your internet connection.
    pause
    exit /b 1
)
echo        Done.
echo.

REM ── 4. Copy config template ────────────────────────────────────────────────
if exist "config.py" (
    echo  [SKIP] config.py already exists
) else (
    echo  [3/5] Copying config.example.py → config.py...
    copy /Y config.example.py config.py >nul
    echo        Done.
    echo        NOTE: Open config.py and add your API keys (News, Discord, etc.)
)
echo.

REM ── 5. Create data directory from examples ─────────────────────────────────
if exist "data\" (
    echo  [SKIP] data\ directory already exists
) else (
    echo  [4/5] Creating data\ directory from data.example\...
    mkdir data
    xcopy /E /I /Q data.example\* data\ >nul
    echo        Done.
)
echo.

REM ── 6. Done ────────────────────────────────────────────────────────────────
echo  [5/5] Setup complete!
echo.
echo  =============================================
echo   ✅  Everything is ready!
echo  =============================================
echo.
echo  To run the app:
echo.
echo    .venv\Scripts\python.exe main.py
echo.
echo  Or activate the venv first:
echo.
echo    .venv\Scripts\activate
echo    python main.py
echo.
echo  To enable experimental internal modules:
echo    python main.py --internal
echo.
pause
