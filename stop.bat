@echo off
title Calorie Agent STOP Script
echo ==============================================
echo [Calorie Agent] Stopping Servers...
echo ==============================================

echo 1. Closing console windows...
taskkill /FI "WindowTitle eq CalorieBackend*" /T /F 2>NUL
taskkill /FI "WindowTitle eq Administrator:  CalorieBackend*" /T /F 2>NUL
taskkill /FI "WindowTitle eq CalorieFrontend*" /T /F 2>NUL
taskkill /FI "WindowTitle eq Administrator:  CalorieFrontend*" /T /F 2>NUL

echo 2. Killing all remaining python/node processes on ports...
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr "LISTENING" ^| findstr ":8000"') DO (
    taskkill /F /PID %%T 2>NUL
)
FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| findstr "LISTENING" ^| findstr ":3000"') DO (
    taskkill /F /PID %%T 2>NUL
)

echo 3. Final cleanup of zombie python processes...
taskkill /F /IM python.exe 2>NUL

timeout /t 2 /nobreak >NUL

echo ==============================================
echo All servers have been successfully stopped!
echo ==============================================
pause
