@echo off
title RON - Local AI Agent Launcher
echo ===================================================
echo   RON: Local, Offline, and Safe Desktop Agent
echo ===================================================
echo.
echo Checking Python setup and installing/verifying dependencies...
py -m pip install customtkinter pyautogui keyboard Pillow --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed! Please check python installation.
    pause
    exit /b %errorlevel%
)

echo.
echo Launching Ron desktop interface silently...
start "" pyw -m ron_agent.ron_ui
exit
