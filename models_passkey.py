"""Passkey (WebAuthn) models for passwordless authentication."""

from datetime import datetime
from models import db


class Passkey(db.Model):
    """WebAuthn/Passkey credentials for passwordless authentication."""

    __tablename__ = 'passkeys'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # WebAuthn credential data
    credential_id = db.Column(db.LargeBinary, nullable=False, unique=True)  # Binary credential ID
    public_key = db.Column(db.LargeBinary, nullable=False)  # Public key for verification
    sign_count = db.Column(db.Integer, default=0)  # Counter to prevent replay attacks

    # Credential metadata
    name = db.Column(db.String(100))  # User-friendly name (e.g., "iPhone 13", "YubiKey")
    aaguid = db.Column(db.String(36))  # Authenticator AAGUID
    transports = db.Column(db.String(200))  # Comma-separated list (usb,nfc,ble,internal)

    # Device information
    device_type = db.Column(db.String(50))  # platform (Face ID, Touch ID) or cross-platform (YubiKey)
    user_agent = db.Column(db.String(255))  # Browser/device info
    ip_address = db.Column(db.String(45))  # IP when registered

    # Status and usage
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Backup status
    is_backup_eligible = db.Column(db.Boolean, default=False)  # Can be synced across devices
    is_backup_state = db.Column(db.Boolean, default=False)  # Currently backed up

    # Relationship
    user = db.relationship('User', backref='passkeys')

    def __repr__(self):
        return f'<Passkey {self.name} for User {self.user_id}>'

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'device_type': self.device_type,
            'transports': self.transports.split(',') if self.transports else [],
            'created_at': self.created_at.isoformat(),
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'is_active': self.is_active,
            'is_backup_eligible': self.is_backup_eligible
        }


class PasskeyChallenge(db.Model):
    """Temporary challenges for WebAuthn registration and authentication."""

    __tablename__ = 'passkey_challenges'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for login challenges

    challenge = db.Column(db.String(255), nullable=False, unique=True)  # Random challenge
    challenge_type = db.Column(db.String(20), nullable=False)  # 'registration' or 'authentication'

    # Associated data
    email = db.Column(db.String(120))  # Email for authentication challenges
    expires_at = db.Column(db.DateTime, nullable=False)  # Challenge expires in 5 minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='passkey_challenges')

    def __repr__(self):
        return f'<PasskeyChallenge {self.challenge_type} for {self.email or self.user_id}>'

    def is_expired(self):
        """Check if challenge has expired."""
        return datetime.utcnow() > self.expires_at
