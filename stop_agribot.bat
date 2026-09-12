@echo off
REM Stops the AgriBot backend and frontend dev servers.

echo Stopping AgriBot servers...
taskkill /FI "WINDOWTITLE eq AgriBot Backend*" /T /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq AgriBot Frontend*" /T /F > nul 2>&1
echo Done. If a window is still open, you can close it manually.
pause
