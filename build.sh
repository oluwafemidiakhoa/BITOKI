#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
export FLASK_APP=app.py
python -m flask db upgrade || python init_db.py

echo "Build completed successfully!"
