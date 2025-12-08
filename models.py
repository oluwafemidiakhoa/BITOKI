"""Database models for BITOKI platform."""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
import pyotp

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    """User account model."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))

    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)

    # KYC status
    kyc_level = db.Column(db.Integer, default=0)  # 0=none, 1=basic, 2=intermediate, 3=advanced
    kyc_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

    # Security
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    wallets = db.relationship('Wallet', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True, foreign_keys='Transaction.user_id')
    kyc_documents = db.relationship('KYCDocument', backref='user', lazy=True, foreign_keys='KYCDocument.user_id')

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check if password is correct."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def generate_2fa_secret(self):
        """Generate 2FA secret."""
        self.two_factor_secret = pyotp.random_base32()
        return self.two_factor_secret

    def get_2fa_uri(self):
        """Get 2FA QR code URI."""
        if not self.two_factor_secret:
            self.generate_2fa_secret()
        return pyotp.totp.TOTP(self.two_factor_secret).provisioning_uri(
            name=self.email,
            issuer_name='BITOKI'
        )

    def verify_2fa_token(self, token):
        """Verify 2FA token."""
        if not self.two_factor_secret:
            return False
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(token, valid_window=1)

    def __repr__(self):
        return f'<User {self.username}>'


class Wallet(db.Model):
    """User wallet for different cryptocurrencies."""

    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    currency = db.Column(db.String(10), nullable=False)  # BTC, ETH, SOL, USDT, NGN
    balance = db.Column(db.Float, default=0.0)
    address = db.Column(db.String(255))  # Deposit address

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'currency', name='unique_user_currency'),
    )

    def __repr__(self):
        return f'<Wallet {self.currency}: {self.balance}>'


class Transaction(db.Model):
    """Transaction history."""

    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal, trade, transfer
    currency = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, default=0.0)

    # Transaction details
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, cancelled
    tx_hash = db.Column(db.String(255))  # Blockchain transaction hash
    address = db.Column(db.String(255))  # Destination/Source address

    # For trades
    from_currency = db.Column(db.String(10))
    to_currency = db.Column(db.String(10))
    exchange_rate = db.Column(db.Float)

    # Reference
    reference = db.Column(db.String(100), unique=True)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Transaction {self.type} {self.amount} {self.currency}>'


class KYCDocument(db.Model):
    """KYC verification documents."""

    __tablename__ = 'kyc_documents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Document type
    document_type = db.Column(db.String(50), nullable=False)  # NIN, BVN, passport, drivers_license, utility_bill
    document_number = db.Column(db.String(100))

    # File paths
    front_image = db.Column(db.String(255))
    back_image = db.Column(db.String(255))
    selfie_image = db.Column(db.String(255))

    # Verification
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    rejection_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<KYCDocument {self.document_type} - {self.status}>'


class BankAccount(db.Model):
    """User bank accounts for NGN deposits/withdrawals."""

    __tablename__ = 'bank_accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)

    is_verified = db.Column(db.Boolean, default=False)
    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='bank_accounts')

    def __repr__(self):
        return f'<BankAccount {self.bank_name} - {self.account_number}>'


class Trade(db.Model):
    """Trading orders and history."""

    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Trade details
    order_type = db.Column(db.String(20), nullable=False)  # buy, sell, swap
    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)

    amount = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, default=0.0)

    # Order status
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled, failed
    order_id = db.Column(db.String(100), unique=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='trades')

    def __repr__(self):
        return f'<Trade {self.order_type} {self.from_currency}/{self.to_currency}>'


class GiftCardTrade(db.Model):
    """Gift card trading history."""

    __tablename__ = 'giftcard_trades'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Card details
    brand = db.Column(db.String(50), nullable=False)
    card_type = db.Column(db.String(50))
    face_value = db.Column(db.Float, nullable=False)

    # Trade details
    trade_type = db.Column(db.String(10), nullable=False)  # buy, sell
    rate = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)

    # Card info (for sells)
    card_code = db.Column(db.String(100))
    card_pin = db.Column(db.String(50))
    card_image = db.Column(db.String(255))

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, rejected
    rejection_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='giftcard_trades')

    def __repr__(self):
        return f'<GiftCardTrade {self.brand} - {self.trade_type}>'


class SavingsPlan(db.Model):
    """Crypto savings plans."""

    __tablename__ = 'savings_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    currency = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    apy = db.Column(db.Float, nullable=False)

    # Plan details
    plan_type = db.Column(db.String(20), default='flexible')  # flexible, locked
    lock_period = db.Column(db.Integer)  # Days (for locked plans)

    interest_earned = db.Column(db.Float, default=0.0)
    last_interest_date = db.Column(db.DateTime)

    # Status
    status = db.Column(db.String(20), default='active')  # active, completed, withdrawn

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    maturity_date = db.Column(db.DateTime)
    withdrawn_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='savings_plans')

    def __repr__(self):
        return f'<SavingsPlan {self.currency} - {self.amount}>'


class ActivityLog(db.Model):
    """User activity logging for security."""

    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    action = db.Column(db.String(50), nullable=False)  # login, logout, password_change, etc.
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    details = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='activity_logs')

    def __repr__(self):
        return f'<ActivityLog {self.action} at {self.created_at}>'
