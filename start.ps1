param (
    [string]$mode = "all"
)

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "                    VitaLens AI Health Navigator                      " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Backend API Docs : http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "  Admin Web Portal : http://localhost:3000  (admin@vitalens.health / admin123)" -ForegroundColor Gray
Write-Host "  Mobile Expo App  : Port 8081" -ForegroundColor Gray
Write-Host "======================================================================`n" -ForegroundColor Cyan

switch ($mode.ToLower()) {
    "all" {
        Write-Host "[*] Starting Backend (:8000), Admin Web (:3000), and Mobile Expo (:8081)..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\backend'; if (Test-Path 'venv\Scripts\Activate.ps1') { . .\venv\Scripts\Activate.ps1 }; python main.py"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\admin-web'; npm run dev"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\mobile'; npx expo start"
    }
    "core" {
        Write-Host "[*] Starting Backend (:8000) and Mobile Expo (:8081)..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\backend'; if (Test-Path 'venv\Scripts\Activate.ps1') { . .\venv\Scripts\Activate.ps1 }; python main.py"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\mobile'; npx expo start"
    }
    "backend" {
        Write-Host "[*] Starting Backend (:8000)..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\backend'; if (Test-Path 'venv\Scripts\Activate.ps1') { . .\venv\Scripts\Activate.ps1 }; python main.py"
    }
    "mobile" {
        Write-Host "[*] Starting Mobile Expo (:8081)..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\mobile'; npx expo start"
    }
    "web" {
        Write-Host "[*] Starting Mobile Expo in Web Browser mode (:8081)..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\mobile'; npx expo start --web"
    }
    "admin" {
        Write-Host "[*] Starting Admin Web Portal (:3000)..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\admin-web'; npm run dev"
    }
    "install" {
        Write-Host "[*] Installing all dependencies across Root, Mobile, Admin, and Backend..." -ForegroundColor Yellow
        npm run install:all
    }
    "test" {
        Write-Host "[*] Running backend tests..." -ForegroundColor Yellow
        Set-Location "$rootDir\backend"
        if (Test-Path 'venv\Scripts\Activate.ps1') { . .\venv\Scripts\Activate.ps1 }
        pytest -v
    }
    default {
        Write-Host "Unknown mode: '$mode'." -ForegroundColor Red
        Write-Host "Available modes: all, core, backend, mobile, web, admin, install, test" -ForegroundColor Yellow
    }
}
