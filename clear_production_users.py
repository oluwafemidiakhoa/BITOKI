#!/usr/bin/env python3
"""Clear all users from production database."""

import psycopg2
import os
from urllib.parse import urlparse

def clear_production_users():
    """Clear all users from production PostgreSQL database."""
    
    # Production database URL from environment
    database_url = "postgresql://bitoki_user:Xjs1CzQpKLEyA13lPVtJGW4zJZAF8l5T@dpg-ct92kcpu0jms73ckkdp0-a.oregon-postgres.render.com/bitoki_wkby"
    
    try:
        # Parse database URL
        result = urlparse(database_url)
        
        # Connect to database with SSL
        conn = psycopg2.connect(
            host=result.hostname,
            port=result.port or 5432,
            database=result.path[1:],
            user=result.username,
            password=result.password,
            sslmode='require'
        )
        
        cursor = conn.cursor()
        
        print("Clearing all user data from production database...")
        
        # Delete in order to respect foreign key constraints
        cursor.execute("DELETE FROM passkey_challenges;")
        cursor.execute("DELETE FROM passkeys;")
        cursor.execute("DELETE FROM activity_logs;")
        cursor.execute("DELETE FROM transactions;") 
        cursor.execute("DELETE FROM wallets;")
        cursor.execute("DELETE FROM users;")
        
        # Reset any auto-increment sequences
        cursor.execute("ALTER SEQUENCE users_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE wallets_id_seq RESTART WITH 1;")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("SUCCESS: Production database cleared successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: clearing production database: {e}")
        return False

if __name__ == "__main__":
    print("BITOKI Production Database Cleanup")
    print("=" * 40)
    
    if clear_production_users():
        print("\nSUCCESS: Production database cleanup completed!")
        print("You can now register fresh accounts for testing.")
    else:
        print("\nFAILED: Production database cleanup failed!")