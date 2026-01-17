#!/usr/bin/env python3
"""Check what type of database is being used and if passkey tables exist."""

import os
from app import app, db
import models_passkey

def check_database():
    """Check database configuration and passkey tables."""
    with app.app_context():
        try:
            # Get database URL
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"Database URL type: {'PostgreSQL' if 'postgresql' in db_url else 'SQLite' if 'sqlite' in db_url else 'Other'}")
            print(f"Database URL: {db_url[:50]}...")
            
            # Check if passkey tables exist
            try:
                from models_passkey import PasskeyChallenge
                result = PasskeyChallenge.query.limit(1).all()
                print("SUCCESS: passkey_challenges table exists and is accessible")
            except Exception as e:
                print(f"ERROR: passkey_challenges table issue: {e}")
            
            try:
                from models_passkey import Passkey
                result = Passkey.query.limit(1).all()
                print("SUCCESS: passkeys table exists and is accessible")
            except Exception as e:
                print(f"ERROR: passkeys table issue: {e}")
                
        except Exception as e:
            print(f"Database check failed: {e}")

if __name__ == "__main__":
    print("Database Configuration Check")
    print("=" * 40)
    check_database()