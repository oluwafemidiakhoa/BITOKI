"""Comprehensive security manager for BITOKI platform."""

import os
import hashlib
import hmac
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pyotp
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from loguru import logger


@dataclass
class SecurityAlert:
    """Represents a security alert."""
    alert_id: str
    user_id: str
    alert_type: str  # login, transfer, suspicious_activity
    message: str
    timestamp: str
    is_read: bool = False
    severity: str = "medium"  # low, medium, high, critical


@dataclass
class TwoFactorAuth:
    """Represents 2FA configuration for a user."""
    user_id: str
    secret: str
    method: str  # totp, sms, email
    backup_codes: List[str]
    enabled: bool = False
    created_at: str = ""
    last_used: str = ""


@dataclass
class EncryptedWallet:
    """Represents an encrypted wallet."""
    user_id: str
    currency: str
    encrypted_balance: str
    salt: str
    last_updated: str
    version: int = 1


@dataclass
class TransactionRecord:
    """Represents an immutable transaction record."""
    transaction_id: str
    user_id: str
    type: str  # deposit, withdrawal, trade, giftcard
    amount: float
    currency: str
    timestamp: str
    status: str
    previous_hash: str = ""
    current_hash: str = ""
    metadata: Dict = None


class SecurityManager:
    """Main security manager for the BITOKI platform."""

    def __init__(self, encryption_key: str = None):
        """
        Initialize security manager.
        
        Args:
            encryption_key: Optional encryption key (generate if None)
        """
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # In-memory storage (in production, use database)
        self.two_factor_auths: Dict[str, TwoFactorAuth] = {}
        self.security_alerts: Dict[str, List[SecurityAlert]] = {}
        self.encrypted_wallets: Dict[str, List[EncryptedWallet]] = {}
        self.transaction_chain: List[TransactionRecord] = []
        
        logger.info("Security manager initialized")

    def _generate_encryption_key(self) -> str:
        """Generate a secure encryption key."""
        return Fernet.generate_key().decode()

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _generate_salt(self) -> str:
        """Generate a random salt."""
        return os.urandom(16).hex()

    def _calculate_hash(self, data: str) -> str:
        """Calculate SHA-256 hash of data."""
        return hashlib.sha256(data.encode()).hexdigest()

    # 2FA Methods
    def setup_2fa(self, user_id: str, method: str = "totp") -> TwoFactorAuth:
        """
        Set up two-factor authentication for a user.
        
        Args:
            user_id: User ID
            method: Authentication method (totp, sms, email)
        
        Returns:
            TwoFactorAuth object
        """
        if user_id in self.two_factor_auths:
            raise ValueError(f"2FA already set up for user {user_id}")

        # Generate secret
        secret = pyotp.random_base32()
        
        # Generate backup codes
        backup_codes = [pyotp.random_base32(10) for _ in range(5)]
        
        two_factor = TwoFactorAuth(
            user_id=user_id,
            secret=secret,
            method=method,
            backup_codes=backup_codes,
            enabled=True,
            created_at=datetime.now().isoformat(),
            last_used=""
        )
        
        self.two_factor_auths[user_id] = two_factor
        
        # Generate QR code URI for TOTP
        if method == "totp":
            issuer = "BITOKI"
            uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user_id,
                issuer_name=issuer
            )
            logger.info(f"2FA setup for {user_id}. QR URI: {uri}")
        
        return two_factor

    def verify_2fa_code(self, user_id: str, code: str) -> bool:
        """
        Verify a 2FA code.
        
        Args:
            user_id: User ID
            code: 2FA code to verify
        
        Returns:
            True if code is valid
        """
        if user_id not in self.two_factor_auths:
            return False

        two_factor = self.two_factor_auths[user_id]
        
        if not two_factor.enabled:
            return False

        # Check if it's a backup code
        if code in two_factor.backup_codes:
            # Remove used backup code
            two_factor.backup_codes.remove(code)
            two_factor.last_used = datetime.now().isoformat()
            return True

        # Verify TOTP code
        totp = pyotp.TOTP(two_factor.secret)
        is_valid = totp.verify(code)
        
        if is_valid:
            two_factor.last_used = datetime.now().isoformat()
        
        return is_valid

    def disable_2fa(self, user_id: str) -> bool:
        """
        Disable 2FA for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            True if successfully disabled
        """
        if user_id in self.two_factor_auths:
            self.two_factor_auths[user_id].enabled = False
            return True
        return False

    # Wallet Encryption
    def encrypt_wallet_balance(self, user_id: str, currency: str, balance: float, password: str) -> EncryptedWallet:
        """
        Encrypt a wallet balance.
        
        Args:
            user_id: User ID
            currency: Currency code
            balance: Balance amount
            password: User password for key derivation
        
        Returns:
            EncryptedWallet object
        """
        # Generate salt
        salt = self._generate_salt()
        salt_bytes = salt.encode()
        
        # Derive key from password
        key = self._derive_key(password, salt_bytes)
        cipher_suite = Fernet(key)
        
        # Encrypt balance
        encrypted_balance = cipher_suite.encrypt(str(balance).encode()).decode()
        
        wallet = EncryptedWallet(
            user_id=user_id,
            currency=currency,
            encrypted_balance=encrypted_balance,
            salt=salt,
            last_updated=datetime.now().isoformat()
        )
        
        # Store wallet
        if user_id not in self.encrypted_wallets:
            self.encrypted_wallets[user_id] = []
        
        # Replace existing wallet for this currency
        self.encrypted_wallets[user_id] = [
            w for w in self.encrypted_wallets[user_id] 
            if w.currency != currency
        ]
        self.encrypted_wallets[user_id].append(wallet)
        
        return wallet

    def decrypt_wallet_balance(self, user_id: str, currency: str, password: str) -> float:
        """
        Decrypt a wallet balance.
        
        Args:
            user_id: User ID
            currency: Currency code
            password: User password
        
        Returns:
            Decrypted balance
        """
        if user_id not in self.encrypted_wallets:
            raise ValueError(f"No encrypted wallets found for user {user_id}")
        
        # Find wallet for currency
        wallet = None
        for w in self.encrypted_wallets[user_id]:
            if w.currency == currency:
                wallet = w
                break
        
        if not wallet:
            raise ValueError(f"No encrypted wallet found for {currency}")
        
        # Derive key
        salt_bytes = wallet.salt.encode()
        key = self._derive_key(password, salt_bytes)
        cipher_suite = Fernet(key)
        
        # Decrypt balance
        try:
            decrypted = cipher_suite.decrypt(wallet.encrypted_balance.encode())
            return float(decrypted.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt wallet: {e}")
            raise ValueError("Invalid password or corrupted data")

    # Transaction Integrity
    def add_transaction(self, transaction_data: Dict) -> TransactionRecord:
        """
        Add a transaction to the immutable chain.
        
        Args:
            transaction_data: Transaction data
        
        Returns:
            TransactionRecord with hash
        """
        # Create transaction record
        record = TransactionRecord(
            transaction_id=transaction_data.get("transaction_id", f"tx_{int(time.time() * 1000)}"),
            user_id=transaction_data["user_id"],
            type=transaction_data["type"],
            amount=transaction_data["amount"],
            currency=transaction_data["currency"],
            timestamp=transaction_data.get("timestamp", datetime.now().isoformat()),
            status=transaction_data.get("status", "completed"),
            metadata=transaction_data.get("metadata")
        )
        
        # Set previous hash (last transaction in chain)
        if self.transaction_chain:
            record.previous_hash = self.transaction_chain[-1].current_hash
        
        # Calculate current hash
        data_str = f"{record.transaction_id}{record.user_id}{record.type}{record.amount}{record.currency}{record.timestamp}{record.status}{record.previous_hash}"
        record.current_hash = self._calculate_hash(data_str)
        
        # Add to chain
        self.transaction_chain.append(record)
        
        return record

    def verify_transaction_chain(self) -> bool:
        """
        Verify the integrity of the transaction chain.
        
        Returns:
            True if chain is valid
        """
        if not self.transaction_chain:
            return True
        
        for i in range(1, len(self.transaction_chain)):
            current = self.transaction_chain[i]
            previous = self.transaction_chain[i-1]
            
            # Check if current transaction points to previous hash
            if current.previous_hash != previous.current_hash:
                return False
            
            # Verify current hash
            data_str = f"{current.transaction_id}{current.user_id}{current.type}{current.amount}{current.currency}{current.timestamp}{current.status}{current.previous_hash}"
            expected_hash = self._calculate_hash(data_str)
            
            if current.current_hash != expected_hash:
                return False
        
        return True

    def get_transaction_history(self, user_id: str) -> List[TransactionRecord]:
        """
        Get transaction history for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of transaction records
        """
        return [t for t in self.transaction_chain if t.user_id == user_id]

    # Alert System
    def create_alert(self, user_id: str, alert_type: str, message: str, severity: str = "medium") -> SecurityAlert:
        """
        Create a security alert.
        
        Args:
            user_id: User ID
            alert_type: Type of alert
            message: Alert message
            severity: Severity level
        
        Returns:
            SecurityAlert object
        """
        alert = SecurityAlert(
            alert_id=f"alert_{int(time.time() * 1000)}",
            user_id=user_id,
            alert_type=alert_type,
            message=message,
            timestamp=datetime.now().isoformat(),
            is_read=False,
            severity=severity
        )
        
        if user_id not in self.security_alerts:
            self.security_alerts[user_id] = []
        
        self.security_alerts[user_id].append(alert)
        
        # In production, send push notification/email
        logger.info(f"Security alert created: {alert_type} for {user_id}")
        
        return alert

    def get_alerts(self, user_id: str, unread_only: bool = False) -> List[SecurityAlert]:
        """
        Get security alerts for a user.
        
        Args:
            user_id: User ID
            unread_only: Only return unread alerts
        
        Returns:
            List of security alerts
        """
        if user_id not in self.security_alerts:
            return []
        
        alerts = self.security_alerts[user_id]
        
        if unread_only:
            return [a for a in alerts if not a.is_read]
        
        return alerts

    def mark_alert_as_read(self, user_id: str, alert_id: str) -> bool:
        """
        Mark an alert as read.
        
        Args:
            user_id: User ID
            alert_id: Alert ID
        
        Returns:
            True if successfully marked as read
        """
        if user_id not in self.security_alerts:
            return False
        
        for alert in self.security_alerts[user_id]:
            if alert.alert_id == alert_id:
                alert.is_read = True
                return True
        
        return False

    # Biometric Support (simulated)
    def register_biometric(self, user_id: str, biometric_data: str) -> bool:
        """
        Register biometric data for a user.
        
        Args:
            user_id: User ID
            biometric_data: Biometric data (hash or token)
        
        Returns:
            True if successfully registered
        """
        # In production, this would interface with device biometric APIs
        # For simulation, we store a hash of the biometric data
        biometric_hash = self._calculate_hash(biometric_data)
        
        # Store in user's security profile (simulated)
        logger.info(f"Biometric registered for {user_id}")
        return True

    def verify_biometric(self, user_id: str, biometric_data: str) -> bool:
        """
        Verify biometric data.
        
        Args:
            user_id: User ID
            biometric_data: Biometric data to verify
        
        Returns:
            True if biometric data is valid
        """
        # In production, this would use device biometric APIs
        # For simulation, we return True (as if biometric was verified)
        logger.info(f"Biometric verification for {user_id}")
        return True

    # Fraud Protection
    def check_fraud_patterns(self, transaction_data: Dict) -> Tuple[bool, str]:
        """
        Check for fraudulent patterns in transactions.
        
        Args:
            transaction_data: Transaction data to check
        
        Returns:
            Tuple of (is_fraudulent, reason)
        """
        # Simple fraud detection rules
        amount = transaction_data.get("amount", 0)
        user_id = transaction_data.get("user_id")
        transaction_type = transaction_data.get("type")
        
        # Check for unusually large transactions
        if amount > 10000:  # $10,000 threshold
            return True, "Large transaction amount requires verification"
        
        # Check for rapid successive transactions
        recent_transactions = self.get_transaction_history(user_id)
        recent_transactions = [t for t in recent_transactions 
                              if datetime.fromisoformat(t.timestamp) > datetime.now() - timedelta(minutes=5)]
        
        if len(recent_transactions) > 3:
            return True, "Multiple rapid transactions detected"
        
        # Check for unusual transaction types
        if transaction_type == "withdrawal" and amount > 5000:
            return True, "Large withdrawal requires additional verification"
        
        return False, "No fraud detected"

    # Password Security
    def hash_password(self, password: str) -> str:
        """
        Hash a password using PBKDF2.
        
        Args:
            password: Password to hash
        
        Returns:
            Hashed password
        """
        salt = self._generate_salt()
        salt_bytes = salt.encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt_bytes,
            iterations=100000,
            backend=default_backend()
        )
        
        hash = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return f"{salt}${hash.decode()}"

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            password: Password to verify
            hashed_password: Hashed password
        
        Returns:
            True if password matches
        """
        try:
            salt, hash = hashed_password.split("$")
            salt_bytes = salt.encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_bytes,
                iterations=100000,
                backend=default_backend()
            )
            
            new_hash = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return new_hash.decode() == hash
        except Exception:
            return False

    # Session Security
    def generate_session_token(self, user_id: str) -> str:
        """
        Generate a secure session token.
        
        Args:
            user_id: User ID
        
        Returns:
            Session token
        """
        timestamp = str(int(time.time()))
        data = f"{user_id}{timestamp}{self.encryption_key}"
        return self._calculate_hash(data)

    def verify_session_token(self, user_id: str, token: str) -> bool:
        """
        Verify a session token.
        
        Args:
            user_id: User ID
            token: Session token to verify
        
        Returns:
            True if token is valid
        """
        # Generate expected token
        expected_token = self.generate_session_token(user_id)
        return hmac.compare_digest(token, expected_token)