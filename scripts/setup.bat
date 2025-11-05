@echo off
REM Setup script for Windows
REM Installs dependencies and verifies installation

echo ========================================
echo Audio-to-Sign-Language Converter Setup
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Check pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not installed
    pause
    exit /b 1
)

echo [OK] pip found
echo.

REM Install dependencies
echo Installing dependencies...
echo This may take a few minutes...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Dependencies installed!
echo.

REM Run verification
echo Running verification...
python scripts\verify_setup.py

if errorlevel 1 (
    echo.
    echo [WARNING] Some components may be missing
    echo Please check the output above
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Run: scripts\run.bat
echo   2. Open: http://localhost:5001
echo.
pause

