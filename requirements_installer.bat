@echo off
cd /d %~dp0

REM Pip'i güncelle
echo Upgrading pip...
pip install --upgrade pip
if %errorlevel% neq 0 (
    echo Failed to upgrade pip
    pause
    exit /b %errorlevel%
)

REM Gereksinimleri yükle
echo Installing requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements
    pause
    exit /b %errorlevel%
)

echo All dependencies installed successfully.
pause
