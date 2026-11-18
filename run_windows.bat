@echo off
rem Wormhole Runner launcher for Windows. Needs Python 3.10+ (https://www.python.org/downloads/).
cd /d "%~dp0"
set "PY=python"
where py >nul 2>nul && set "PY=py -3"
if not exist ".venv\Scripts\python.exe" (
    %PY% -m venv .venv
    if errorlevel 1 (
        echo Could not create a virtual environment. Is Python 3.10+ installed?
        pause
        exit /b 1
    )
)
call ".venv\Scripts\activate.bat"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
python main.py
if errorlevel 1 pause
