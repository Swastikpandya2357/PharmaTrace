@echo off
title PharmaTrace SCN Server
color 0F
cls
echo ======================================================================
echo           PHARMATRACE - SUPPLY CHAIN NETWORK (SCN) SERVER
echo ======================================================================
echo.
echo  Port: 8000
echo  Access URLs:
echo    - Main Portal:  http://127.0.0.1:8000/
echo    - Django Admin: http://127.0.0.1:8000/admin/login/
echo.
echo  Admin Credentials:
echo    - Email / User: pandyaswastik2005@gmail.com / Swastik Pandya
echo    - Password:     sompandya
echo.
echo  To stop the server: Press Ctrl+C or run STOP_SERVER.bat
echo ======================================================================
echo.

cd /d "D:\task3\proj"

:: Check if port 8000 is already in use
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %ERRORLEVEL% equ 0 (
    echo [WARNING] Port 8000 is already in use by another process.
    echo Stopping old instance...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
    timeout /t 1 >nul
)

:RUN_LOOP
echo [%DATE% %TIME%] Starting Django Server on 0.0.0.0:8000...
"C:\Program Files\Python313\python.exe" manage.py runserver 0.0.0.0:8000
echo.
echo [INFO] Server stopped or crashed. Auto-restarting in 3 seconds...
echo Press Ctrl+C to abort.
timeout /t 3
goto RUN_LOOP
