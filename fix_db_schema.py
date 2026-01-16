#!/usr/bin/env python3
"""Fix database schema by adding missing columns."""

import os
import psycopg2
from urllib.parse import urlparse

def fix_database_schema():
    """Add missing columns to users table."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("No DATABASE_URL found, skipping schema fix")
        return
    
    try:
        # Parse database URL
        result = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        
        cursor = conn.cursor()
        
        # Add missing columns to users table
        columns_to_add = [
            ("password_reset_token", "VARCHAR(255)"),
            ("password_reset_expires", "TIMESTAMP"),
            ("email_verification_token", "VARCHAR(255)"),
            ("email_verification_sent_at", "TIMESTAMP")
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type};")
                print(f"✅ Added column: {column_name}")
            except psycopg2.errors.DuplicateColumn:
                print(f"⏭️  Column already exists: {column_name}")
            except Exception as e:
                print(f"❌ Error adding {column_name}: {e}")
        
        # Create passkey tables
        create_passkey_tables = [
            """
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
            """,
            """
            CREATE TABLE IF NOT EXISTS passkey_challenges (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                challenge VARCHAR(255) NOT NULL UNIQUE,
                challenge_type VARCHAR(20) NOT NULL,
                email VARCHAR(120),
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        
        for table_sql in create_passkey_tables:
            try:
                cursor.execute(table_sql)
                print(f"✅ Created passkey table")
            except Exception as e:
                print(f"❌ Error creating passkey table: {e}")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 Database schema fix completed!")
        
    except Exception as e:
        print(f"❌ Database schema fix failed: {e}")

if __name__ == '__main__':
    fix_database_schema()