@echo off
REM Starts both AgriBot servers and opens the app in your browser.
REM Just double-click this file any time you want to use AgriBot.

set PROJECT_DIR=%~dp0

echo Starting AgriBot backend...
start "AgriBot Backend" cmd /k "cd /d "%PROJECT_DIR%backend" && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo Starting AgriBot frontend...
start "AgriBot Frontend" cmd /k "cd /d "%PROJECT_DIR%frontend" && npm run dev"

echo Waiting for servers to start...
timeout /t 8 /nobreak > nul

echo Opening AgriBot in your browser...
start http://localhost:5173

echo.
echo AgriBot is starting up in two separate windows (Backend and Frontend).
echo Keep both of those windows open while you use the app.
echo Close them (or just close this window's children) when you're done.
echo.
pause
