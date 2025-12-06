#!/bin/bash
cd "$(dirname "$0")"

echo "=================================================="
echo "   Google Maps AI Bot - Server Launcher"
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

echo ""
echo "🚀 Starting Flask Server..."
echo "Server will run at http://localhost:5000"
echo ""
echo "To connect with LINE, you need to run ngrok in another terminal:"
echo "   ngrok http 5000"
echo ""

python app.py
