@echo off
rem SENTIA — avvio alternativo (doppio click)
cd /d "%~dp0"
start "" pythonw server.py 2>nul || start "" python server.py
timeout /t 2 /nobreak >nul
start "" http://localhost:7107/
