@echo off
REM Machining Formulas V2 Launcher for Windows
REM This script ensures proper Python environment with tkinter support

echo 🔧 Machining Formulas V2 Launcher
echo ==================================

REM Check for Python with tkinter support
echo 📋 Python environment check...

set PYTHON_CMD=
for %%P in (python python3 py -3.11 py -3.10) do (
    %%P --version >nul 2>&1
    if !errorlevel! neq 0 (
        %%P -c "import tkinter" >nul 2>&1
        if !errorlevel! equ 0 (
            set PYTHON_CMD=%%P
            echo ✅ Found compatible Python:
            %%P --version
            goto :found_python
        )
    )
)

:found_python
if "%PYTHON_CMD%"=="" (
    echo ❌ ERROR: No Python with tkinter support found!
    echo.
    echo 🔧 Solutions:
    echo 1. Install Python from python.org (includes tkinter)
    echo 2. Install python-tk package: pip install tk
    echo 3. Use conda: conda install tk
    echo.
    pause
    exit /b 1
)

REM Check if required modules are installed
echo.
echo 📦 Checking required modules...

set MISSING_MODULES=
python -c "import requests" >nul 2>&1
if !errorlevel! neq 0 set MISSING_MODULES=%MISSING_MODULES% requests

python -c "import markdown" >nul 2>&1
if !errorlevel! neq 0 set MISSING_MODULES=%MISSING_MODULES% markdown

if not "%MISSING_MODULES%"=="" (
    echo.
    echo ❌ Missing modules: %MISSING_MODULES%
    echo 📦 Installing missing modules...
    
    if exist requirements_v2.txt (
        %PYTHON_CMD% -m pip install -r requirements_v2.txt
    ) else (
        %PYTHON_CMD% -m pip install requests markdown
    )
    
    if !errorlevel! neq 0 (
        echo ❌ Failed to install required modules
        pause
        exit /b 1
    )
)

echo.
echo 🚀 Starting Machining Formulas V2...
echo 📍 Using: %PYTHON_CMD%
echo 📁 Working directory: %CD%
echo.

REM Launch V2 GUI
%PYTHON_CMD% v2_gui.py

if !errorlevel! neq 0 (
    echo.
    echo ❌ Failed to start V2 GUI
    echo 🔧 Troubleshooting:
    echo 1. Check if v2_gui.py exists in current directory
    echo 2. Verify all dependencies are installed
    echo 3. Check Python version compatibility
    pause
    exit /b 1
)

echo.
echo ✅ V2 GUI closed successfully
pause