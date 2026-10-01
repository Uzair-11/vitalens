@echo off
title VitaLens Project Launcher
cls
echo ===================================================
echo           VitaLens AI Health Navigator
echo ===================================================
echo [1] Start All (Backend + Admin Web + Mobile Expo)
echo [2] Start Backend Only (FastAPI on :8000)
echo [3] Start Mobile Only (Expo on :8081)
echo [4] Start Admin Web Only (Vite on :3000)
echo [5] Exit
echo ===================================================
set /p choice="Select an option [1-5]: "

if "%choice%"=="1" (
    echo Starting Backend, Admin Web, and Mobile Expo...
    start "VitaLens Backend" cmd /k "cd backend && python main.py"
    start "VitaLens Admin Web" cmd /k "cd admin-web && npm run dev"
    start "VitaLens Mobile" cmd /k "cd mobile && npx expo start"
    exit /b
)
if "%choice%"=="2" (
    start "VitaLens Backend" cmd /k "cd backend && python main.py"
    exit /b
)
if "%choice%"=="3" (
    start "VitaLens Mobile" cmd /k "cd mobile && npx expo start"
    exit /b
)
if "%choice%"=="4" (
    start "VitaLens Admin Web" cmd /k "cd admin-web && npm run dev"
    exit /b
)
if "%choice%"=="5" (
    exit /b
)
