"""Email service for sending notifications."""

from flask_mail import Mail, Message
from flask import current_app, render_template_string
import secrets
from datetime import datetime, timedelta

mail = Mail()


def init_mail(app):
    """Initialize Flask-Mail with the app."""
    mail.init_app(app)


def send_email(to, subject, body, html=None):
    """
    Send an email.

    Args:
        to: Recipient email address (string or list)
        subject: Email subject
        body: Plain text body
        html: HTML body (optional)
    """
    try:
        msg = Message(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[to] if isinstance(to, str) else to,
            body=body,
            html=html
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to}: {str(e)}")
        return False


def send_verification_email(user, verification_token):
    """Send email verification email."""
    verify_url = f"http://127.0.0.1:5000/auth/verify-email?token={verification_token}"

    subject = "Verify Your BITOKI Email Address"

    body = f"""
Hello {user.username},

Welcome to BITOKI! Please verify your email address to activate your account.

Click the link below to verify your email:
{verify_url}

This link will expire in 24 hours.

If you didn't create a BITOKI account, please ignore this email.

Best regards,
The BITOKI Team
"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .warning {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to BITOKI!</h1>
            <p>Verify Your Email Address</p>
        </div>
        <div class="content">
            <h2>Hello {user.username},</h2>
            <p>Thank you for creating a BITOKI account! To get started, please verify your email address.</p>

            <div style="text-align: center;">
                <a href="{verify_url}" class="button">Verify Email Address</a>
            </div>

            <div class="warning">
                <strong>⏱️ This link will expire in 24 hours.</strong>
            </div>

            <p>If you didn't create a BITOKI account, please ignore this email.</p>

            <p>Best regards,<br>The BITOKI Team</p>
        </div>
    </div>
</body>
</html>
"""

    return send_email(user.email, subject, body, html)


def send_welcome_email(user):
    """Send welcome email to new user."""
    subject = "Welcome to BITOKI - Your Crypto Trading Journey Starts Here!"

    body = f"""
Hello {user.username},

Welcome to BITOKI! We're excited to have you join our cryptocurrency trading platform.

Your account has been successfully created:
- Email: {user.email}
- Username: {user.username}
- KYC Level: {user.kyc_level}

Getting Started:
1. Complete your KYC verification to unlock higher trading limits
2. Enable Two-Factor Authentication (2FA) for enhanced security
3. Explore our trading features and start buying/selling crypto

Need Help?
Visit our FAQ: https://bitoki.com/help/faq
Contact Support: support@bitoki.com

Best regards,
The BITOKI Team

---
This is an automated message. Please do not reply to this email.
"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        .steps {{ background: white; padding: 20px; border-left: 4px solid #667eea; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to BITOKI!</h1>
            <p>Your Crypto Trading Journey Starts Here</p>
        </div>
        <div class="content">
            <h2>Hello {user.username},</h2>
            <p>We're excited to have you join our cryptocurrency trading platform.</p>

            <div class="steps">
                <h3>Your Account Details:</h3>
                <ul>
                    <li><strong>Email:</strong> {user.email}</li>
                    <li><strong>Username:</strong> {user.username}</li>
                    <li><strong>KYC Level:</strong> {user.kyc_level}</li>
                </ul>
            </div>

            <div class="steps">
                <h3>Getting Started:</h3>
                <ol>
                    <li>Complete your KYC verification to unlock higher trading limits</li>
                    <li>Enable Two-Factor Authentication (2FA) for enhanced security</li>
                    <li>Explore our trading features and start buying/selling crypto</li>
                </ol>
            </div>

            <div style="text-align: center;">
                <a href="https://bitoki.com/dashboard" class="button">Go to Dashboard</a>
            </div>

            <p><strong>Need Help?</strong></p>
            <p>Visit our <a href="https://bitoki.com/help/faq">FAQ</a> or contact <a href="mailto:support@bitoki.com">support@bitoki.com</a></p>
        </div>
        <div class="footer">
            <p>&copy; 2025 BITOKI. All rights reserved.</p>
            <p>This is an automated message. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""

    return send_email(user.email, subject, body, html)


def send_login_alert(user, ip_address, user_agent, location="Unknown"):
    """Send login alert email."""
    subject = "New Login to Your BITOKI Account"

    body = f"""
Hello {user.username},

We detected a new login to your BITOKI account:

Login Details:
- Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- IP Address: {ip_address}
- Device: {user_agent}
- Location: {location}

If this was you, you can safely ignore this email.

If this wasn't you, please:
1. Change your password immediately
2. Enable Two-Factor Authentication (2FA)
3. Contact our support team

Stay safe,
The BITOKI Team
"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .alert {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin: 20px 0; }}
        .details {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .warning {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="alert">
            <h2>🔐 New Login Detected</h2>
            <p>We detected a new login to your BITOKI account.</p>
        </div>

        <div class="details">
            <h3>Login Details:</h3>
            <ul>
                <li><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</li>
                <li><strong>IP Address:</strong> {ip_address}</li>
                <li><strong>Device:</strong> {user_agent}</li>
                <li><strong>Location:</strong> {location}</li>
            </ul>
        </div>

        <p>If this was you, you can safely ignore this email.</p>

        <div class="warning">
            <h3>⚠️ If this wasn't you:</h3>
            <ol>
                <li>Change your password immediately</li>
                <li>Enable Two-Factor Authentication (2FA)</li>
                <li>Contact our support team at support@bitoki.com</li>
            </ol>
        </div>

        <p>Stay safe,<br>The BITOKI Team</p>
    </div>
</body>
</html>
"""

    return send_email(user.email, subject, body, html)


def send_password_reset_email(user, reset_token):
    """Send password reset email."""
    reset_url = f"https://bitoki.com/auth/reset-password?token={reset_token}"

    subject = "Reset Your BITOKI Password"

    body = f"""
Hello {user.username},

You requested to reset your BITOKI account password.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this, please ignore this email and your password will remain unchanged.

Best regards,
The BITOKI Team
"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{ display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .warning {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Reset Your Password</h2>
        <p>Hello {user.username},</p>
        <p>You requested to reset your BITOKI account password.</p>

        <div style="text-align: center;">
            <a href="{reset_url}" class="button">Reset Password</a>
        </div>

        <div class="warning">
            <strong>⏱️ This link will expire in 1 hour.</strong>
        </div>

        <p>If you didn't request this, please ignore this email and your password will remain unchanged.</p>

        <p>Best regards,<br>The BITOKI Team</p>
    </div>
</body>
</html>
"""

    return send_email(user.email, subject, body, html)


def send_transaction_alert(user, transaction_type, amount, currency):
    """Send transaction alert email."""
    subject = f"BITOKI Transaction Alert: {transaction_type.upper()} {amount} {currency}"

    body = f"""
Hello {user.username},

A transaction was made on your BITOKI account:

Transaction Details:
- Type: {transaction_type.upper()}
- Amount: {amount} {currency}
- Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

If you didn't authorize this transaction, please contact support immediately.

Best regards,
The BITOKI Team
"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .transaction {{ background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 20px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>💰 Transaction Alert</h2>
        <p>Hello {user.username},</p>
        <p>A transaction was made on your BITOKI account.</p>

        <div class="transaction">
            <h3>Transaction Details:</h3>
            <ul>
                <li><strong>Type:</strong> {transaction_type.upper()}</li>
                <li><strong>Amount:</strong> {amount} {currency}</li>
                <li><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</li>
            </ul>
        </div>

        <p>If you didn't authorize this transaction, please contact support immediately at support@bitoki.com</p>

        <p>Best regards,<br>The BITOKI Team</p>
    </div>
</body>
</html>
"""

    return send_email(user.email, subject, body, html)


def send_kyc_status_email(user, status, rejection_reason=None):
    """Send KYC verification status email."""
    if status == 'approved':
        subject = "✅ KYC Verification Approved - BITOKI"
        message = "Congratulations! Your KYC verification has been approved."
        color = "#28a745"
    elif status == 'rejected':
        subject = "❌ KYC Verification Rejected - BITOKI"
        message = f"Your KYC verification was rejected. Reason: {rejection_reason}"
        color = "#dc3545"
    else:
        subject = "📋 KYC Verification Under Review - BITOKI"
        message = "Your KYC documents are being reviewed. We'll notify you within 24-48 hours."
        color = "#ffc107"

    body = f"""
Hello {user.username},

{message}

Current KYC Level: {user.kyc_level}

Best regards,
The BITOKI Team
"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .status {{ background: {color}; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="status">
            <h2>KYC Verification Status</h2>
        </div>
        <p>Hello {user.username},</p>
        <p>{message}</p>
        <p><strong>Current KYC Level:</strong> {user.kyc_level}</p>
        <p>Best regards,<br>The BITOKI Team</p>
    </div>
</body>
</html>
"""

    return send_email(user.email, subject, body, html)
