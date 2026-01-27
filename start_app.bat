@echo off
echo Starting Career Miner App...

:: Check if Flask is installed, install if not
python -c "import flask" 2>NUL
if %errorlevel% neq 0 (
    echo Flask not found. Installing...
    pip install flask
)

:: Start the browser in a separate process after a short delay
start "" "http://127.0.0.1:5000"

:: Run the Flask app
python app.py

pause
