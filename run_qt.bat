@echo off
echo Starting GenVR Batch Processor (PySide6 Version)...
echo.
echo Checking Python installation...
python --version
echo.

if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install -r requirements.txt

echo.
echo Launching PySide6 application...
python main_qt.py

pause

