"""Email service for sending notifications and alerts."""

import os
import smtplib
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, List, Optional
from jinja2 import Environment, FileSystemLoader
from loguru import logger


class EmailService:
    """Handles sending emails via SMTP."""

    def __init__(self, config_path: str = "config/email_config.yaml"):
        """
        Initialize email service.
        
        Args:
            config_path: Path to email configuration file
        """
        self.config = self._load_config(config_path)
        self.templates = self._setup_templates()
        
        # Test SMTP connection
        self._test_smtp_connection()

    def _load_config(self, config_path: str) -> Dict:
        """Load email configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load email config: {e}")
            raise

    def _setup_templates(self) -> Environment:
        """Set up Jinja2 template environment."""
        template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'web', 'templates', 'emails')
        
        # Create templates directory if it doesn't exist
        os.makedirs(template_dir, exist_ok=True)
        
        return Environment(loader=FileSystemLoader(template_dir))

    def _test_smtp_connection(self) -> bool:
        """Test SMTP connection."""
        try:
            smtp_config = self.config['email']['smtp']
            
            # Create connection
            if smtp_config['use_ssl']:
                server = smtplib.SMTP_SSL(smtp_config['host'], smtp_config['port'])
            else:
                server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
                if smtp_config['use_tls']:
                    server.starttls()
            
            # Login
            server.login(smtp_config['username'], smtp_config['password'])
            server.quit()
            
            logger.info("SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False

    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_vars: Dict = None,
        attachments: List[Dict] = None
    ) -> bool:
        """
        Send an email using a template.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Template file name (without .html)
            template_vars: Variables for template
            attachments: List of attachment dicts with 'filename' and 'content'
        
        Returns:
            True if email was sent successfully
        """
        if template_vars is None:
            template_vars = {}
        if attachments is None:
            attachments = []
        
        try:
            # Load template
            template = self.templates.get_template(f"{template_name}.html")
            html_content = template.render(**template_vars)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.config['email']['sender']['name']} <{self.config['email']['sender']['email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Add attachments
            for attachment in attachments:
                part = MIMEApplication(attachment['content'])
                part.add_header('Content-Disposition', 'attachment', filename=attachment['filename'])
                msg.attach(part)
            
            # Send email
            smtp_config = self.config['email']['smtp']
            
            if smtp_config['use_ssl']:
                server = smtplib.SMTP_SSL(smtp_config['host'], smtp_config['port'])
            else:
                server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
                if smtp_config['use_tls']:
                    server.starttls()
            
            server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_login_alert(self, user_email: str, user_id: str, ip_address: str, device_info: str) -> bool:
        """
        Send a login alert email.
        
        Args:
            user_email: User's email address
            user_id: User ID
            ip_address: IP address of login
            device_info: Device information
        
        Returns:
            True if alert was sent
        """
        template_vars = {
            'user_id': user_id,
            'ip_address': ip_address,
            'device_info': device_info,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.send_email(
            to_email=user_email,
            subject=self.config['email']['templates']['login_alert']['subject'],
            template_name='login_alert',
            template_vars=template_vars
        )

    def send_transfer_alert(self, user_email: str, amount: float, currency: str, transaction_id: str) -> bool:
        """
        Send a transfer alert email.
        
        Args:
            user_email: User's email address
            amount: Transfer amount
            currency: Currency
            transaction_id: Transaction ID
        
        Returns:
            True if alert was sent
        """
        template_vars = {
            'amount': amount,
            'currency': currency,
            'transaction_id': transaction_id,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.send_email(
            to_email=user_email,
            subject=self.config['email']['templates']['transfer_alert']['subject'],
            template_name='transfer_alert',
            template_vars=template_vars
        )

    def send_2fa_setup_email(self, user_email: str, qr_code_url: str, backup_codes: List[str]) -> bool:
        """
        Send 2FA setup email with QR code and backup codes.
        
        Args:
            user_email: User's email address
            qr_code_url: URL or data for QR code
            backup_codes: List of backup codes
        
        Returns:
            True if email was sent
        """
        template_vars = {
            'qr_code_url': qr_code_url,
            'backup_codes': backup_codes
        }
        
        return self.send_email(
            to_email=user_email,
            subject=self.config['email']['templates']['two_factor_setup']['subject'],
            template_name='2fa_setup',
            template_vars=template_vars
        )

    def send_backup_codes_email(self, user_email: str, backup_codes: List[str]) -> bool:
        """
        Send backup codes email.
        
        Args:
            user_email: User's email address
            backup_codes: List of backup codes
        
        Returns:
            True if email was sent
        """
        template_vars = {
            'backup_codes': backup_codes
        }
        
        return self.send_email(
            to_email=user_email,
            subject=self.config['email']['templates']['backup_codes']['subject'],
            template_name='backup_codes',
            template_vars=template_vars
        )

    def create_email_templates(self) -> None:
        """Create default email templates if they don't exist."""
        template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'web', 'templates', 'emails')
        
        templates = {
            'login_alert.html': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #007bff; color: white; padding: 10px; text-align: center; }
        .content { padding: 20px; background-color: #f8f9fa; }
        .alert { background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; }
        .footer { text-align: center; color: #6c757d; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🔒 BITOKI Security Alert</h2>
        </div>
        <div class="content">
            <p>Hello,</p>
            <div class="alert">
                <p><strong>New login detected on your BITOKI account.</strong></p>
                <p><strong>User ID:</strong> {{ user_id }}</p>
                <p><strong>IP Address:</strong> {{ ip_address }}</p>
                <p><strong>Device:</strong> {{ device_info }}</p>
                <p><strong>Time:</strong> {{ timestamp }}</p>
            </div>
            <p>If this was you, you can safely ignore this alert.</p>
            <p>If you don't recognize this activity, please secure your account immediately by:</p>
            <ol>
                <li>Changing your password</li>
                <li>Enabling two-factor authentication</li>
                <li>Contacting our support team</li>
            </ol>
            <p>Thank you for using BITOKI!</p>
        </div>
        <div class="footer">
            <p>© {{ "now"|strftime("%Y") }} BITOKI. All rights reserved.</p>
            <p>This is an automated message. Please do not reply.</p>
        </div>
    </div>
</body>
</html>''',
            
            'transfer_alert.html': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #28a745; color: white; padding: 10px; text-align: center; }
        .content { padding: 20px; background-color: #f8f9fa; }
        .alert { background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; }
        .footer { text-align: center; color: #6c757d; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>💰 BITOKI Transfer Confirmation</h2>
        </div>
        <div class="content">
            <p>Hello,</p>
            <div class="alert">
                <p><strong>Your transfer has been processed successfully.</strong></p>
                <p><strong>Amount:</strong> {{ amount }} {{ currency }}</p>
                <p><strong>Transaction ID:</strong> {{ transaction_id }}</p>
                <p><strong>Time:</strong> {{ timestamp }}</p>
            </div>
            <p>Thank you for using BITOKI for your transactions!</p>
            <p>If you didn't authorize this transfer, please contact our support team immediately.</p>
        </div>
        <div class="footer">
            <p>© {{ "now"|strftime("%Y") }} BITOKI. All rights reserved.</p>
            <p>This is an automated message. Please do not reply.</p>
        </div>
    </div>
</body>
</html>''',
            
            '2fa_setup.html': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #6c757d; color: white; padding: 10px; text-align: center; }
        .content { padding: 20px; background-color: #f8f9fa; }
        .backup-codes { background-color: #e9ecef; padding: 15px; font-family: monospace; }
        .footer { text-align: center; color: #6c757d; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🔐 Two-Factor Authentication Setup</h2>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>You have successfully enabled two-factor authentication for your BITOKI account.</p>
            
            <h3>Scan this QR code with your authenticator app:</h3>
            <p><img src="{{ qr_code_url }}" alt="QR Code" width="200"></p>
            
            <h3>Your Backup Codes:</h3>
            <div class="backup-codes">
                {% for code in backup_codes %}
                <p>{{ code }}</p>
                {% endfor %}
            </div>
            
            <p><strong>Important:</strong> Please store these backup codes in a safe place. They can be used to access your account if you lose your authenticator device.</p>
            <p>Each backup code can only be used once.</p>
        </div>
        <div class="footer">
            <p>© {{ "now"|strftime("%Y") }} BITOKI. All rights reserved.</p>
            <p>This is an automated message. Please do not reply.</p>
        </div>
    </div>
</body>
</html>''',
            
            'backup_codes.html': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #ffc107; color: white; padding: 10px; text-align: center; }
        .content { padding: 20px; background-color: #f8f9fa; }
        .backup-codes { background-color: #fff3cd; padding: 15px; font-family: monospace; }
        .footer { text-align: center; color: #6c757d; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🔑 Your BITOKI Backup Codes</h2>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>Here are your backup codes for two-factor authentication:</p>
            
            <div class="backup-codes">
                {% for code in backup_codes %}
                <p>{{ code }}</p>
                {% endfor %}
            </div>
            
            <p><strong>Important:</strong> Please store these backup codes in a safe place. They can be used to access your account if you lose your authenticator device.</p>
            <p>Each backup code can only be used once.</p>
        </div>
        <div class="footer">
            <p>© {{ "now"|strftime("%Y") }} BITOKI. All rights reserved.</p>
            <p>This is an automated message. Please do not reply.</p>
        </div>
    </div>
</body>
</html>'''
        }
        
        for filename, content in templates.items():
            filepath = os.path.join(template_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    f.write(content)
                logger.info(f"Created email template: {filename}")

    def send_test_email(self, to_email: str) -> bool:
        """
        Send a test email.
        
        Args:
            to_email: Recipient email address
        
        Returns:
            True if test email was sent
        """
        template_vars = {
            'test_message': 'This is a test email from BITOKI.'
        }
        
        return self.send_email(
            to_email=to_email,
            subject="🧪 BITOKI Test Email",
            template_name='test',
            template_vars=template_vars
        )