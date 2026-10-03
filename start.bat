@echo off
setlocal EnableDelayedExpansion
title VitaLens Project Launcher
cd /d "%~dp0"

:MENU
cls
color 0B
echo ======================================================================
echo                    VitaLens AI Health Navigator
echo ======================================================================
echo.
echo   [1] Start Full Stack (Backend + Admin Web + Mobile Expo)
echo   [2] Start App Core (Backend + Mobile Expo)
echo   [3] Start Backend Only (FastAPI on http://localhost:8000)
echo   [4] Start Mobile Expo Only (Metro on http://localhost:8081)
echo   [5] Start Mobile in Web Browser (Expo Web on http://localhost:8081)
echo   [6] Start Admin Web Portal Only (Vite on http://localhost:3000)
echo   [7] Install All Dependencies (pip + npm across all 3 services)
echo   [8] Run Backend Health Check and Pytest Suite
echo   [9] Exit
echo.
echo ----------------------------------------------------------------------
echo   Quick Reference:
echo   - Backend API Docs : http://localhost:8000/docs
echo   - Admin Web Portal : http://localhost:3000  (admin@vitalens.health / admin123)
echo   - Mobile Expo App  : Port 8081 (Scan QR code with Expo Go)
echo ======================================================================
echo.

set /p choice="Select an option [1-9]: "

if "%choice%"=="1" goto START_ALL
if "%choice%"=="2" goto START_CORE
if "%choice%"=="3" goto START_BACKEND
if "%choice%"=="4" goto START_MOBILE
if "%choice%"=="5" goto START_MOBILE_WEB
if "%choice%"=="6" goto START_ADMIN
if "%choice%"=="7" goto INSTALL_ALL
if "%choice%"=="8" goto RUN_TESTS
if "%choice%"=="9" goto EXIT
goto INVALID

:START_ALL
echo.
echo [*] Launching Backend, Admin Web, and Mobile Expo in separate windows...
start "VitaLens Backend [Port 8000]" cmd /k "cd /d "%~dp0backend" && (if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat) && (if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat) && python main.py"
start "VitaLens Admin Web [Port 3000]" cmd /k "cd /d "%~dp0admin-web" && npm run dev"
start "VitaLens Mobile Expo [Port 8081]" cmd /k "cd /d "%~dp0mobile" && npx expo start"
echo [OK] All services launched!
timeout /t 3 >nul
exit /b

:START_CORE
echo.
echo [*] Launching Backend and Mobile Expo...
start "VitaLens Backend [Port 8000]" cmd /k "cd /d "%~dp0backend" && (if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat) && (if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat) && python main.py"
start "VitaLens Mobile Expo [Port 8081]" cmd /k "cd /d "%~dp0mobile" && npx expo start"
echo [OK] Core services launched!
timeout /t 3 >nul
exit /b

:START_BACKEND
echo.
echo [*] Launching FastAPI Backend on http://localhost:8000...
start "VitaLens Backend [Port 8000]" cmd /k "cd /d "%~dp0backend" && (if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat) && (if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat) && python main.py"
exit /b

:START_MOBILE
echo.
echo [*] Launching Expo Mobile App on port 8081...
start "VitaLens Mobile Expo [Port 8081]" cmd /k "cd /d "%~dp0mobile" && npx expo start"
exit /b

:START_MOBILE_WEB
echo.
echo [*] Launching Expo Mobile App in Web Browser mode...
start "VitaLens Mobile Web [Port 8081]" cmd /k "cd /d "%~dp0mobile" && npx expo start --web"
exit /b

:START_ADMIN
echo.
echo [*] Launching Admin Web Portal on http://localhost:3000...
start "VitaLens Admin Web [Port 3000]" cmd /k "cd /d "%~dp0admin-web" && npm run dev"
exit /b

:INSTALL_ALL
echo.
echo ======================================================================
echo             Installing All Dependencies across Services
echo ======================================================================
echo.
echo [1/3] Installing Root Dependencies...
call npm install
echo.
echo [2/3] Installing Mobile and Admin NPM Dependencies...
call npm install --prefix mobile
call npm install --prefix admin-web
echo.
echo [3/3] Installing Python Backend Requirements...
cd /d "%~dp0backend"
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
pip install -r requirements.txt
cd /d "%~dp0"
echo.
echo [OK] All dependencies successfully installed!
pause
goto MENU

:RUN_TESTS
echo.
echo ======================================================================
echo                     Running Backend Test Suite
echo ======================================================================
cd /d "%~dp0backend"
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
pytest -v
cd /d "%~dp0"
pause
goto MENU

:INVALID
echo [!] Invalid selection. Please choose a number between 1 and 9.
timeout /t 2 >nul
goto MENU

:EXIT
exit /b
