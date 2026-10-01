param (
    [string]$mode = "all"
)

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "          VitaLens AI Health Navigator             " -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan

switch ($mode.ToLower()) {
    "all" {
        Write-Host "Starting Backend, Admin Web, and Mobile Expo..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python main.py"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd admin-web; npm run dev"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd mobile; npx expo start"
    }
    "backend" {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python main.py"
    }
    "mobile" {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd mobile; npx expo start"
    }
    "admin" {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd admin-web; npm run dev"
    }
    "web" {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd mobile; npx expo start --web"
    }
    default {
        Write-Host "Unknown mode: $mode. Available modes: all, backend, mobile, admin, web" -ForegroundColor Red
    }
}
