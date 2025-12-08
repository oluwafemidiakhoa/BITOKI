@echo off
REM Installation script for BITOKI trading bot (Windows)

echo ==================================
echo BITOKI Trading Bot - Installation
echo ==================================
echo.

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo uv is not installed
    echo Please install uv first:
    echo   PowerShell: irm https://astral.sh/uv/install.ps1 ^| iex
    echo   Or visit: https://github.com/astral-sh/uv
    pause
    exit /b 1
)

echo Installing Python dependencies...
uv pip install -e .

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Copy .env.example to .env and add your API credentials
echo 2. Review config/strategy_config.yaml
echo 3. Run: uv run python run.py
echo.
echo See SETUP.md for detailed setup instructions
echo.
pause
