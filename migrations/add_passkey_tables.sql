-- Migration: Add Passkey Authentication Tables
-- Date: 2025-01-01
-- Description: Creates tables for WebAuthn/Passkey passwordless authentication

-- Table for storing passkey credentials
CREATE TABLE IF NOT EXISTS passkeys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    credential_id BLOB NOT NULL UNIQUE,
    public_key BLOB NOT NULL,
    sign_count INTEGER DEFAULT 0,
    name VARCHAR(100),
    aaguid VARCHAR(100),
    device_type VARCHAR(50),
    transports VARCHAR(200),
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    is_backup_eligible BOOLEAN DEFAULT 0,
    is_backup_state BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table for storing temporary authentication challenges
CREATE TABLE IF NOT EXISTS passkey_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    email VARCHAR(120),
    challenge VARCHAR(255) NOT NULL UNIQUE,
    challenge_type VARCHAR(20) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_passkeys_user_id ON passkeys(user_id);
CREATE INDEX IF NOT EXISTS idx_passkeys_credential_id ON passkeys(credential_id);
CREATE INDEX IF NOT EXISTS idx_passkeys_is_active ON passkeys(is_active);
CREATE INDEX IF NOT EXISTS idx_passkey_challenges_user_id ON passkey_challenges(user_id);
CREATE INDEX IF NOT EXISTS idx_passkey_challenges_email ON passkey_challenges(email);
CREATE INDEX IF NOT EXISTS idx_passkey_challenges_challenge ON passkey_challenges(challenge);
CREATE INDEX IF NOT EXISTS idx_passkey_challenges_expires_at ON passkey_challenges(expires_at);
