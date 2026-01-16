#!/usr/bin/env python3
"""Create missing passkey tables in database."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db
import models_passkey  # Import to register passkey models
from app import app

def create_passkey_tables():
    """Create passkey-related tables."""
    with app.app_context():
        try:
            print("Creating passkey tables...")
            
            # Create all tables (will only create missing ones)
            db.create_all()
            
            print("✅ Passkey tables created successfully!")
            print("Tables created:")
            print("- passkeys")
            print("- passkey_challenges")
            
        except Exception as e:
            print(f"❌ Error creating passkey tables: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("BITOKI Passkey Tables Creation")
    print("=" * 40)
    
    if create_passkey_tables():
        print("\n✅ Database setup completed successfully!")
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1)