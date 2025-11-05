@echo off
REM Quick start script for Windows
REM This script runs the Flask server

echo ========================================
echo Audio-to-Sign-Language Converter
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "server.py" (
    echo [ERROR] server.py not found
    echo Please run this script from the AudioToSignLanguageConverter directory
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Flask not found. Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting server...
echo Open your browser to: http://localhost:5001
echo Press Ctrl+C to stop the server
echo.

python server.py

pause

