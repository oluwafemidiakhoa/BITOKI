#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database (only if it doesn't exist)
python init_db.py || true

echo "Build completed successfully!"
