@echo off
cd /d "%~dp0"
echo Installing dependencies...
"t:/officeservices/Billing Clerk/DASHBOARD/.python313/python.exe" -m pip install flask flask-cors
echo.
echo Starting Deriv Trading Bot Dashboard...
echo Open your browser to: http://localhost:5000
echo.
"t:/officeservices/Billing Clerk/DASHBOARD/.python313/python.exe" app.py
pause
