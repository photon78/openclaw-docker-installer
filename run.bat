@echo off
REM OpenClaw Installer — launcher for Windows
REM Activates venv automatically, creates it if missing.

set SCRIPT_DIR=%~dp0
set VENV=%SCRIPT_DIR%.venv

if not exist "%VENV%\Scripts\python.exe" (
    echo Setting up virtual environment...
    python -m venv "%VENV%"
    if exist "%SCRIPT_DIR%requirements.txt" (
        "%VENV%\Scripts\pip" install --quiet -r "%SCRIPT_DIR%requirements.txt"
    )
    "%VENV%\Scripts\pip" install --quiet -e "%SCRIPT_DIR%.[dev]"
    echo Done.
)

"%VENV%\Scripts\python.exe" "%SCRIPT_DIR%src\main.py" %*
