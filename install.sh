#!/bin/bash
# Installation script for BITOKI trading bot

echo "=================================="
echo "BITOKI Trading Bot - Installation"
echo "=================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed"
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed"
else
    echo "✅ uv is already installed"
fi

echo ""
echo "Installing Python dependencies..."
uv pip install -e .

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and add your API credentials"
echo "2. Review config/strategy_config.yaml"
echo "3. Run: uv run python run.py"
echo ""
echo "See SETUP.md for detailed setup instructions"
echo ""
