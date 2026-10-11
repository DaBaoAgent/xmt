@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
if not exist logs mkdir logs
echo. >> logs\run.log
echo ==== %date% %time% ==== >> logs\run.log
".venv\Scripts\python.exe" snapshot.py >> logs\run.log 2>&1
echo exit=%errorlevel% >> logs\run.log
