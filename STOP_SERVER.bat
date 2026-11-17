@echo off
title Stop PharmaTrace Server
cls
echo ======================================================================
echo              STOPPING PHARMATRACE SCN SERVER
echo ======================================================================
echo.

setlocal enabledelayedexpansion
set FOUND=0

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    set FOUND=1
    echo Found process listening on port 8000 (PID: %%a). Terminating...
    taskkill /F /PID %%a >nul 2>&1
)

if !FOUND! equ 1 (
    echo [SUCCESS] SCN Server has been stopped.
) else (
    echo [INFO] No server was found running on port 8000.
)

echo.
timeout /t 3
