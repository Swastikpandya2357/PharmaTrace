@echo off
title Push PharmaTrace to GitHub
cls
echo ======================================================================
echo                 PUSH PHARMATRACE TO GITHUB
echo ======================================================================
echo.
echo Step 1: Ensure you created an empty repo on GitHub:
echo         https://github.com/new
echo         Name: PharmaTrace
echo.
echo Default URL: https://github.com/Swastikpandya2357/PharmaTrace.git
echo.
set /p REPO_URL="Press ENTER to use default, or paste your repository URL: "
if "%REPO_URL%"=="" set REPO_URL=https://github.com/Swastikpandya2357/PharmaTrace.git

cd /d "D:\task3"

git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%
echo.
echo Pushing to %REPO_URL%...
echo.
git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ======================================================================
    echo [SUCCESS] PharmaTrace is now live on GitHub!
    echo ======================================================================
) else (
    echo.
    echo [INFO] If prompted, complete the sign-in in your browser window.
)
echo.
pause
