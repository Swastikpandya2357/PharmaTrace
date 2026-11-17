@echo off
title Disable Auto-Start on Windows Boot
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SCN_Server.vbs" (
    del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SCN_Server.vbs" >nul
    echo [SUCCESS] Auto-start on boot has been disabled.
) else (
    echo [INFO] Auto-start on boot was not enabled.
)
pause
