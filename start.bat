@echo off
REM Telegram Reminder Bot - Windows Startup Script
REM This script helps with easy deployment and startup on Windows

echo 🤖 Starting Telegram Reminder Bot...

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found!
    echo 📝 Please copy .env.example to .env and configure your settings
    echo copy .env.example .env
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 🏗️  Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo 📦 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Check if bot token is configured
findstr /C:"your_bot_token_here" .env >nul
if %errorlevel% equ 0 (
    echo ❌ Please configure your bot token in .env file!
    echo 📝 Edit .env file and set BOT_TOKEN=your_actual_token
    pause
    exit /b 1
)

echo ✅ Setup complete!
echo 🚀 Starting bot...
echo.

REM Start the bot
python main.py

REM Pause to see any error messages
if %errorlevel% neq 0 (
    echo.
    echo ❌ Bot stopped with error code %errorlevel%
    pause
)
