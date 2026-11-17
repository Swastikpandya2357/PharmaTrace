@echo off
title Enable Auto-Start on Windows Boot
copy /y "D:\task3\START_BACKGROUND.vbs" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SCN_Server.vbs" >nul
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] SCN Server will now start automatically whenever your PC turns on or you log in!
) else (
    echo [ERROR] Failed to copy shortcut to Startup folder.
)
pause
