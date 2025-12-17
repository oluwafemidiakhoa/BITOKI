#!/bin/bash

# BITOKI Local Development Startup Script
# Starts the application on 117.0.0.1:5000

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           BITOKI Local Development Server                   ║"
echo "║                117.0.0.1:5000                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip"
    exit 1
fi

# Install requirements if not already installed
echo "📦 Checking Python dependencies..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "🔄 Installing required packages..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "🚀 Starting BITOKI in development mode..."
echo "   📍 IP Address: 117.0.0.1"
echo "   🕶️  Port: 5000"
echo "   🔒 Security: Development mode (2FA optional)"
echo "   📧 Email: Console output (no actual emails sent)"
echo "   🗃️  Database: SQLite (bitoki_dev.db)"
echo ""

# Set environment variables for local development
export FLASK_ENV=development
export FLASK_APP=app.py
export FLASK_DEBUG=1
export HOST=117.0.0.1
export PORT=5000

echo "🌐 Starting Flask development server..."
echo "   Access the application at: http://117.0.0.1:5000"
echo "   Access the dashboard at: http://117.0.0.1:5000/dashboard"
echo "   Access the API at: http://117.0.0.1:5000/api"
echo ""

# Start the Flask application
python3 app.py

echo ""
echo "❌ Server stopped. Press Ctrl+C to exit."