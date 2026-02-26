@echo off
echo Starting Snagajob Verification...
:: Ensure we run from the script directory
cd /d "%~dp0"

:: basic python check
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Please install Python.
    pause
    exit /b
)

echo Running verify_snagajob.py...
python verify_snagajob.py
echo.
echo Script finished.
pause
