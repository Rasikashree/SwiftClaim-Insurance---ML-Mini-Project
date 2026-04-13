@echo off
echo ==========================================
echo  SwiftClaim — AI Vehicle Claims Platform
echo ==========================================
echo.

REM --- Check Python ---
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+ and add it to PATH.
    pause & exit /b 1
)

REM --- Check Node ---
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 18+ from nodejs.org
    pause & exit /b 1
)

echo [1/2] Installing SwiftClaim backend dependencies...
cd /d "%~dp0swiftclaim\backend"
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 ( echo [ERROR] SwiftClaim install failed. & pause & exit /b 1 )

echo [2/2] Installing frontend dependencies...
cd /d "%~dp0frontend"
call npm install --silent
if %errorlevel% neq 0 ( echo [ERROR] Frontend npm install failed. & pause & exit /b 1 )

echo.
echo Setup complete! Run START.bat to launch all services.
pause
