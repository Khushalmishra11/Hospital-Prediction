@echo off
echo Hospital Prediction System - Quick Start
echo =========================================
echo.

REM Check if running from the correct directory
if not exist "backend" (
    echo Error: Please run this script from the Hospital-Prediction root directory
    exit /b 1
)

echo Starting Backend...
cd backend\app
echo Backend will start on http://localhost:8000
start cmd /k "python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak

echo.
echo Starting Frontend...
cd ..\..
cd frontend
echo Frontend will start on http://localhost:5173
start cmd /k "npm run dev"

echo.
echo ================================================
echo Both servers should be starting now!
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo If you see errors:
echo 1. Make sure you've installed dependencies:
echo    - Backend: pip install -r requirements.txt
echo    - Frontend: npm install
echo 2. Check that .env files are properly configured
echo ================================================
echo.
pause
