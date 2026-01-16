#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Fix database schema first
echo "Fixing database schema..."
python fix_db_schema.py

# Run database migrations
export FLASK_APP=app.py
echo "Running database migrations..."
if python -m flask db upgrade; then
    echo "Database migrations completed successfully"
else
    echo "Migration failed, trying database initialization..."
    python init_db.py
fi

echo "Build completed successfully!"
