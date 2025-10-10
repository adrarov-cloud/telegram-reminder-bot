#!/bin/bash

# Telegram Reminder Bot - Startup Script
# This script helps with easy deployment and startup

set -e

echo "🤖 Starting Telegram Reminder Bot..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📝 Please copy .env.example to .env and configure your settings"
    echo "cp .env.example .env"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🏗️  Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if bot token is configured
if grep -q "your_bot_token_here" .env; then
    echo "❌ Please configure your bot token in .env file!"
    echo "📝 Edit .env file and set BOT_TOKEN=your_actual_token"
    exit 1
fi

echo "✅ Setup complete!"
echo "🚀 Starting bot..."
echo ""

# Start the bot
python main.py
