@echo off
cd /d "%~dp0"

echo Starting Career Miner App...

:: Check if pandas/flask are installed, if not, install all requirements
python -c "import pandas" 2>NUL
if %errorlevel% neq 0 (
    echo Dependencies mismatch or missing. Installing from requirements.txt...
    python -m pip install -r requirements.txt
)

:: Start the browser in a separate process after a short delay
start "" "http://127.0.0.1:5000"

:: Run the Flask app
python app.py

pause
