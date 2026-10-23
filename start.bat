@echo off
title VDOWN - Video Downloader
cd /d "%~dp0"

echo ========================================================
echo   Starting VDOWN Media Downloader...
echo ========================================================

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Initializing...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
)

.venv\Scripts\python.exe run.py
pause
