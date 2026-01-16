#!/usr/bin/env python3
"""Fix production database schema directly."""

import psycopg2
import os

def fix_production_database():
    """Add missing columns and ensure database is properly set up."""
    
    # Production database connection
    database_url = "postgresql://bitoki_user:Xjs1CzQpKLEyA13lPVtJGW4zJZAF8l5T@dpg-ct92kcpu0jms73ckkdp0-a.oregon-postgres.render.com/bitoki_wkby"
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url, sslmode='require')
        cursor = conn.cursor()
        
        print("Connected to production database")
        
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        users_exists = cursor.fetchone()[0]
        print(f"Users table exists: {users_exists}")
        
        if users_exists:
            # Check existing columns
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY column_name;
            """)
            columns = [row[0] for row in cursor.fetchall()]
            print(f"Existing columns: {columns}")
            
            # Add missing columns
            required_columns = {
                'password_reset_token': 'VARCHAR(255)',
                'password_reset_expires': 'TIMESTAMP',
                'email_verification_token': 'VARCHAR(255)',
                'email_verification_sent_at': 'TIMESTAMP'
            }
            
            for column_name, column_type in required_columns.items():
                if column_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type};")
                        print(f"SUCCESS: Added column: {column_name}")
                    except Exception as e:
                        print(f"ERROR adding {column_name}: {e}")
                else:
                    print(f"SKIP: Column already exists: {column_name}")
        
        # Create passkey tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passkeys (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                credential_id BYTEA NOT NULL UNIQUE,
                public_key BYTEA NOT NULL,
                sign_count INTEGER DEFAULT 0,
                name VARCHAR(100),
                aaguid VARCHAR(36),
                transports VARCHAR(200),
                device_type VARCHAR(50),
                user_agent VARCHAR(255),
                ip_address VARCHAR(45),
                is_active BOOLEAN DEFAULT TRUE,
                last_used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_backup_eligible BOOLEAN DEFAULT FALSE,
                is_backup_state BOOLEAN DEFAULT FALSE
            );
        """)
        print("SUCCESS: Ensured passkeys table exists")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passkey_challenges (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                challenge VARCHAR(255) NOT NULL UNIQUE,
                challenge_type VARCHAR(20) NOT NULL,
                email VARCHAR(120),
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("SUCCESS: Ensured passkey_challenges table exists")
        
        # Commit all changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("SUCCESS: Production database fixed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("BITOKI Production Database Fix")
    print("=" * 40)
    fix_production_database()