@echo off
setlocal EnableDelayedExpansion
title VitaLens AI Health Navigator - Full Stack Launcher
cd /d "%~dp0"
color 0B

echo ======================================================================
echo             VitaLens AI Health Navigator - Full Stack
echo                     [1-Click Automated Startup]
echo ======================================================================
echo.

:: ----------------------------------------------------------------------
:: 1. Verify Docker Daemon Status
:: ----------------------------------------------------------------------
echo [*] Checking Docker daemon status...
docker info >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Docker daemon is running.
    goto DOCKER_READY
)

echo [!] Docker is not currently running.
if not exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" goto DOCKER_MANUAL

echo [*] Launching Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo [*] Waiting for Docker daemon to become responsive...
set /a docker_wait=0

:DOCKER_WAIT_LOOP
ping -n 4 127.0.0.1 >nul
docker info >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Docker daemon is ready!
    goto DOCKER_READY
)
set /a docker_wait+=3
echo     Waiting for Docker engine (!docker_wait!s)...
if !docker_wait! geq 60 goto DOCKER_MANUAL
goto DOCKER_WAIT_LOOP

:DOCKER_MANUAL
echo.
echo [!] Please ensure Docker Desktop is running, then press any key to continue...
pause >nul

:DOCKER_READY
echo.

:: ----------------------------------------------------------------------
:: 2. Launch Docker Services (PostgreSQL + FastAPI Backend with V2 Active)
:: ----------------------------------------------------------------------
echo [*] Starting Backend and Database containers via Docker Compose...
docker compose up -d
if %ERRORLEVEL% neq 0 (
    echo [!] Failed to start Docker Compose services. Please check Docker logs.
    pause
    exit /b %ERRORLEVEL%
)
echo [OK] Docker containers are active (FastAPI Backend + PostgreSQL).
echo.

:: ----------------------------------------------------------------------
:: 3. Launch Admin Web Portal (Port 3000)
:: ----------------------------------------------------------------------
echo [*] Launching Admin Web Portal on port 3000...
start "VitaLens Admin Web [Port 3000]" cmd /k "title VitaLens Admin Web [Port 3000] && cd /d "%~dp0admin-web" && npm run dev"
echo [OK] Admin Web process launched.
echo.

:: ----------------------------------------------------------------------
:: 4. Launch Mobile Expo Metro Bundler (Port 8081 - LAN Mode)
:: ----------------------------------------------------------------------
echo [*] Launching Mobile Expo Bundler on port 8081 (LAN mode)...
start "VitaLens Mobile Expo [Port 8081]" cmd /k "title VitaLens Mobile Expo [Port 8081] && cd /d "%~dp0mobile" && npx expo start --lan"
echo [OK] Mobile Expo Bundler launched.
echo.

:: ----------------------------------------------------------------------
:: 5. Master Status Dashboard
:: ----------------------------------------------------------------------
cls
echo ======================================================================
echo              VITALENS FULL-STACK SERVICES ARE NOW LIVE!
echo ======================================================================
echo.
echo   SERVICES AND ENDPOINTS:
echo   ------------------------------------------------------------------
echo   [1] Backend API Docs   : http://localhost:8000/docs
echo   [2] Health and Metrics : http://localhost:8000/health
echo   [3] Admin Web Portal   : http://localhost:3000
echo                            Login: admin@vitalens.health / admin123
echo   [4] Mobile Metro Expo  : http://localhost:8081
echo                            (Scan QR code with Expo Go on your phone)
echo   [5] Active ML Model    : VitaLensSpecialtyNet V2 (specialty-net-v2.0.0)
echo.
echo ======================================================================
echo                           QUICK ACTIONS
echo ======================================================================
echo.
echo   [W] Open Admin Web in Browser       (http://localhost:3000)
echo   [A] Open Backend API Docs           (http://localhost:8000/docs)
echo   [M] Open Metro Bundler in Browser   (http://localhost:8081)
echo   [L] Stream Live Backend Logs
echo   [T] Run Full 55-Test Pytest Suite
echo   [S] Stop All Services (Docker Down)
echo   [Q] Exit Launcher Window (Services stay running in background)
echo.

:ACTION_LOOP
set /p action="Enter action [W/A/M/L/T/S/Q]: "

if /i "!action!"=="W" (
    start http://localhost:3000
    goto ACTION_LOOP
)
if /i "!action!"=="A" (
    start http://localhost:8000/docs
    goto ACTION_LOOP
)
if /i "!action!"=="M" (
    start http://localhost:8081
    goto ACTION_LOOP
)
if /i "!action!"=="L" (
    echo.
    echo [*] Following backend logs (press Ctrl+C to stop streaming)...
    docker compose logs -f backend
    echo.
    goto ACTION_LOOP
)
if /i "!action!"=="T" (
    echo.
    echo [*] Executing backend pytest regression suite...
    docker compose exec backend pytest -v tests
    echo.
    goto ACTION_LOOP
)
if /i "!action!"=="S" (
    echo.
    echo [*] Shutting down Docker containers...
    docker compose down
    echo [OK] Backend services stopped.
    echo [*] Note: You can close the separate Admin Web and Mobile Expo windows.
    pause
    exit /b 0
)
if /i "!action!"=="Q" (
    echo.
    echo [OK] Exiting launcher. All services remain running.
    ping -n 3 127.0.0.1 >nul
    exit /b 0
)

echo [!] Unknown option. Please enter W, A, M, L, T, S, or Q.
goto ACTION_LOOP
