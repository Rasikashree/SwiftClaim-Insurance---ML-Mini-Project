@echo off
echo ==========================================
echo  SwiftClaim — Launching Services
echo ==========================================
echo.
echo Starting SwiftClaim API   (http://localhost:5001)
echo Starting React Frontend   (http://localhost:5173)
echo.
echo [Press Ctrl+C in each window to stop that service]
echo.

REM -- SwiftClaim backend --
start "SwiftClaim API :5001" cmd /k "cd /d "%~dp0swiftclaim\backend" && python app.py"

REM -- React frontend --
timeout /t 3 /nobreak >nul
start "React Frontend :5173" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 5 /nobreak >nul
echo.
echo All services launched! Opening browser...
start http://localhost:5173
