@echo off
title Calorie Agent START Script
echo ==============================================
echo [Calorie Agent] Starting Servers...
echo ==============================================

echo 0. Clearing ports 8000 and 3000...
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr "LISTENING" ^| findstr ":8000"') DO (
    taskkill /F /PID %%T 2>NUL
)
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr "LISTENING" ^| findstr ":3000"') DO (
    taskkill /F /PID %%T 2>NUL
)
timeout /t 2 /nobreak >NUL

echo 1. Starting Backend Server (uvicorn on port 8000)...
cd /d "%~dp0backend"
start "CalorieBackend" cmd /k ".\.venv\Scripts\activate && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo    Waiting for Backend to boot...
timeout /t 5 /nobreak >NUL

echo 2. Starting Frontend Server (Next.js on port 3000)...
cd /d "%~dp0frontend"
start "CalorieFrontend" cmd /k "npm run dev"

cd /d "%~dp0"
echo ==============================================
echo Start complete!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo ==============================================
