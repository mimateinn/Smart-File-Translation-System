@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PY=python"
where py >nul 2>&1
if %ERRORLEVEL%==0 set "PY=py"

if not exist ".venv\Scripts\python.exe" (
    echo Creating a local folder for this app...
    if "%PY%"=="py" (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 (
        echo Please install Python 3.10 or newer, then double-click start.bat again.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
echo Installing needed files...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Could not install the needed files. Check your internet connection and try again.
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" copy ".env.example" ".env" >nul
)

echo Starting the app. A browser window should open soon...
streamlit run app.py
if errorlevel 1 pause
