#!/bin/bash

# BITOKI Local Development Startup Script
# Starts the application on 117.0.0.1:5000

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           BITOKI Local Development Server                   ║"
echo "║                127.0.0.1:5000                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi

# Ensure virtual environment
VENV_DIR=".venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_INSTALL_FLAGS=()

# Prefer virtual environment; fall back to user site-packages if venv is unavailable
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    if ! python3 -m venv "$VENV_DIR"; then
        echo "⚠️ Could not create virtual environment (python3-venv may be missing). Falling back to user site-packages."
        PYTHON_BIN="python3"
        PIP_INSTALL_FLAGS=(--user --break-system-packages)
    fi
fi

if [ "$PYTHON_BIN" = "$VENV_DIR/bin/python" ] && [ -x "$PYTHON_BIN" ]; then
    if "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
        source "$VENV_DIR/bin/activate"
    else
        echo "⚠️ Virtualenv is missing pip. Falling back to system python."
        PYTHON_BIN="python3"
        PIP_INSTALL_FLAGS=(--user --break-system-packages)
    fi
else
    PYTHON_BIN="python3"
    if [ ${#PIP_INSTALL_FLAGS[@]} -eq 0 ]; then
        PIP_INSTALL_FLAGS=(--user --break-system-packages)
    fi
fi

pip_install() {
    local cmd=$1
    shift
    "$PYTHON_BIN" -m pip "$cmd" "${PIP_INSTALL_FLAGS[@]}" "$@"
}

# Install requirements if not already installed
echo "📦 Checking Python dependencies..."
if ! "$PYTHON_BIN" -c "import flask" &> /dev/null; then
    echo "🔄 Installing required packages..."
    pip_install install --upgrade pip
    pip_install install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "🚀 Starting BITOKI in development mode..."
echo "   📍 IP Address: 127.0.0.1"
echo "   🕶️  Port: 5000"
echo "   🔒 Security: Development mode (2FA optional)"
echo "   📧 Email: Console output (no actual emails sent)"
echo "   🗃️  Database: SQLite (bitoki_dev.db)"
echo ""

# Set environment variables for local development
export FLASK_ENV=development
export FLASK_APP=app.py
export FLASK_DEBUG=0
export HOST=127.0.0.1
export PORT=5000

echo "🌐 Starting Flask development server..."
echo "   Access the application at: http://127.0.0.1:5000"
echo "   Access the dashboard at: http://127.0.0.1:5000/dashboard"
echo "   Access the API at: http://127.0.0.1:5000/api"
echo ""

# Start the Flask application
"$PYTHON_BIN" app.py

echo ""
echo "❌ Server stopped. Press Ctrl+C to exit."
