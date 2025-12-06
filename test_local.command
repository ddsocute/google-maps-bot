#!/bin/bash
cd "$(dirname "$0")"

echo "=================================================="
echo "   Google Maps AI Bot - Local Test Launcher"
echo "=================================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and fill in your API keys."
    read -p "Press Enter to exit..."
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦 Installing/Updating dependencies..."
pip install -r requirements.txt -q
playwright install chromium

echo ""
echo "🚀 Starting Local Test..."
echo "Please enter a Google Maps URL when prompted."
echo ""

python test_local.py

echo ""
read -p "Press Enter to exit..."
