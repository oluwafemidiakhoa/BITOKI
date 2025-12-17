"""Authentication routes and handlers."""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Wallet, ActivityLog
import uuid
import secrets
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

# Import limiter from app (will be set by app.py)
limiter = None

def get_limiter():
    """Get the limiter instance from app context."""
    from flask import current_app
    return current_app.extensions.get('limiter')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone')

        # Validation
        if not all([email, username, password]):
            flash('All fields are required', 'error')
            return render_template('auth/register.html')

        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return render_template('auth/register.html')

        # Create user
        user = User(
            email=email,
            username=username,
            phone=phone
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Create default wallets
        currencies = ['BTC', 'ETH', 'SOL', 'USDT', 'NGN']
        for currency in currencies:
            wallet = Wallet(user_id=user.id, currency=currency, balance=0.0)
            db.session.add(wallet)

        db.session.commit()

        # Log activity
        log_activity(user.id, 'register', request.remote_addr, request.headers.get('User-Agent'))

        # Generate email verification token
        verification_token = secrets.token_urlsafe(32)
        user.email_verification_token = verification_token
        user.email_verification_sent_at = datetime.utcnow()
        db.session.commit()

        # Send verification email
        try:
            from services.email_service import send_verification_email
            send_verification_email(user, verification_token)
        except Exception as e:
            print(f"Failed to send verification email: {e}")

        flash('Registration successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been suspended. Contact support.', 'error')
                return render_template('auth/login.html')

            # Check 2FA
            if user.two_factor_enabled:
                session['pending_user_id'] = user.id
                session['remember_me'] = remember
                return redirect(url_for('auth.verify_2fa'))

            # Login user
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Log activity
            log_activity(user.id, 'login', request.remote_addr, request.headers.get('User-Agent'))

            # Send login alert email
            try:
                from services.email_service import send_login_alert
                send_login_alert(user, request.remote_addr, request.headers.get('User-Agent', 'Unknown'), 'Nigeria')
            except Exception as e:
                print(f"Failed to send login alert: {e}")

            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))

        flash('Invalid email or password', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    log_activity(current_user.id, 'logout', request.remote_addr, request.headers.get('User-Agent'))
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Verify 2FA token."""
    user_id = session.get('pending_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        token = request.form.get('token')

        if user.verify_2fa_token(token):
            remember = session.get('remember_me', False)
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Clear session
            session.pop('pending_user_id', None)
            session.pop('remember_me', None)

            log_activity(user.id, 'login_2fa', request.remote_addr, request.headers.get('User-Agent'))

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid 2FA code', 'error')

    return render_template('auth/verify_2fa.html')


@auth_bp.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Setup two-factor authentication."""
    if request.method == 'POST':
        token = request.form.get('token')

        if current_user.verify_2fa_token(token):
            current_user.two_factor_enabled = True
            db.session.commit()
            flash('2FA enabled successfully!', 'success')
            return redirect(url_for('settings'))

        flash('Invalid 2FA code. Please try again.', 'error')

    # Generate QR code
    if not current_user.two_factor_secret:
        current_user.generate_2fa_secret()
        db.session.commit()

    qr_uri = current_user.get_2fa_uri()

    return render_template('auth/setup_2fa.html', qr_uri=qr_uri)


@auth_bp.route('/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    """Disable two-factor authentication."""
    token = request.form.get('token')

    if current_user.verify_2fa_token(token):
        current_user.two_factor_enabled = False
        current_user.two_factor_secret = None
        db.session.commit()
        flash('2FA disabled successfully', 'success')
    else:
        flash('Invalid 2FA code', 'error')

    return redirect(url_for('settings'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password."""
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            # Send password reset email
            try:
                from services.email_service import send_password_reset_email
                send_password_reset_email(user, reset_token)
            except Exception as e:
                print(f"Failed to send password reset email: {e}")

        # Always show success to prevent email enumeration
        flash('If that email exists, we sent a password reset link. Check your email.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password with token."""
    token = request.args.get('token')

    if not token:
        flash('Invalid or missing reset token', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(password_reset_token=token).first()

    if not user or not user.password_reset_expires or user.password_reset_expires < datetime.utcnow():
        flash('Reset token is invalid or has expired', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html', token=token)

        # Update password
        user.set_password(password)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()

        flash('Password reset successful! Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/verify-email', methods=['GET'])
def verify_email():
    """Verify user email address."""
    token = request.args.get('token')

    if not token:
        flash('Invalid verification link', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email_verification_token=token).first()

    if not user:
        flash('Invalid or expired verification link', 'error')
        return redirect(url_for('auth.login'))

    # Check if token is expired (24 hours)
    if user.email_verification_sent_at:
        expiry_time = user.email_verification_sent_at + timedelta(hours=24)
        if datetime.utcnow() > expiry_time:
            flash('Verification link has expired. Please request a new one.', 'error')
            return redirect(url_for('auth.resend_verification'))

    # Verify email
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_sent_at = None
    db.session.commit()

    flash('Email verified successfully! You can now login.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Resend email verification link."""
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user and not user.email_verified:
            # Generate new token
            verification_token = secrets.token_urlsafe(32)
            user.email_verification_token = verification_token
            user.email_verification_sent_at = datetime.utcnow()
            db.session.commit()

            # Send verification email
            try:
                from services.email_service import send_verification_email
                send_verification_email(user, verification_token)
            except Exception as e:
                print(f"Failed to send verification email: {e}")

        # Always show success to prevent email enumeration
        flash('If that email exists and is not verified, we sent a new verification link.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/resend_verification.html')


def log_activity(user_id, action, ip_address, user_agent, details=None):
    """Log user activity."""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )
    db.session.add(log)
    db.session.commit()
