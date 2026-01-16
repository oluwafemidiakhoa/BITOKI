#!/usr/bin/env python3
"""Clear all users from the database for testing."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, User, Wallet, Transaction, ActivityLog
import models_passkey
from app import app

def clear_all_users():
    """Clear all users and related data from database."""
    with app.app_context():
        try:
            print("Clearing all user data from database...")
            
            # Delete in order to respect foreign key constraints
            models_passkey.PasskeyChallenge.query.delete()
            models_passkey.Passkey.query.delete()
            ActivityLog.query.delete()
            Transaction.query.delete()
            Wallet.query.delete()
            User.query.delete()
            
            db.session.commit()
            
            print("✅ All user data cleared successfully!")
            print("You can now register fresh accounts for testing.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error clearing user data: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("BITOKI Database User Cleanup")
    print("=" * 40)
    
    confirm = input("This will delete ALL users and their data. Are you sure? (yes/no): ")
    if confirm.lower() == 'yes':
        if clear_all_users():
            print("\n✅ Database cleanup completed successfully!")
        else:
            print("\n❌ Database cleanup failed!")
            sys.exit(1)
    else:
        print("Operation cancelled.")