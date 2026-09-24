@echo off
title Career Miner - Web Tunnel Hub
cd /d "%~dp0"
echo ===================================================
echo   Starting Career Miner with Cloudflare Web Tunnel
echo ===================================================
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" launch_web_app.py
) else (
    python launch_web_app.py
)
pause
