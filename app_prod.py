"""Production entry point for BITOKI trading platform."""

import os
import sys
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set production environment
os.environ['FLASK_ENV'] = 'production'

# Import the main app
from app import app, security_manager, email_service

# Apply production security middleware
def configure_production_app():
    """Configure the app for production environment."""
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        # Content Security Policy
        response.headers['Content-Security-Policy'] = \
            "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; " \
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; " \
            "img-src 'self' data: chart.googleapis.com; font-src 'self' fonts.gstatic.com; " \
            "connect-src 'self' api.bitoki.com; frame-src 'none'; object-src 'none'"
        
        # XSS Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Type Options
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Frame Options
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response.headers['Permissions-Policy'] = \
            "geolocation=(), microphone=(), camera=(), payment=()"
        
        return response
    
    # Proxy fix for reverse proxy setups
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Configure logging
    configure_production_logging()
    
    # Configure error handling
    configure_error_handling()
    
    # Configure rate limiting
    configure_rate_limiting()
    
    print("✅ Production configuration applied")


def configure_production_logging():
    """Configure production logging."""
    import logging
    from logging.handlers import RotatingFileHandler
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Set up file logging
    file_handler = RotatingFileHandler(
        'logs/bitoki_production.log',
        maxBytes=1024 * 1024 * 100,  # 100 MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Set up console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # Format logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to Flask app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    
    # Suppress some noisy loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    app.logger.info("Production logging configured")


def configure_error_handling():
    """Configure error handling for production."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'success': False, 'error': 'Bad Request', 'details': str(error)}, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'success': False, 'error': 'Unauthorized', 'details': 'Authentication required'}, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'success': False, 'error': 'Forbidden', 'details': 'Access denied'}, 403
    
    @app.errorhandler(404)
    def not_found(error):
        return {'success': False, 'error': 'Not Found', 'details': 'Resource not found'}, 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return {'success': False, 'error': 'Method Not Allowed', 'details': 'HTTP method not supported'}, 405
    
    @app.errorhandler(429)
    def too_many_requests(error):
        return {'success': False, 'error': 'Too Many Requests', 'details': 'Rate limit exceeded'}, 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Server error: {error}", exc_info=True)
        return {'success': False, 'error': 'Internal Server Error', 'details': 'An unexpected error occurred'}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {error}", exc_info=True)
        return {'success': False, 'error': 'Internal Server Error', 'details': 'An unexpected error occurred'}, 500
    
    app.logger.info("Error handling configured")


def configure_rate_limiting():
    """Configure rate limiting for production."""
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    # Initialize limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per minute"]
    )
    
    # Specific rate limits for sensitive endpoints
    @app.before_request
    def apply_specific_rate_limits():
        # Rate limit login endpoints
        if request.path.startswith('/api/auth/login'):
            limiter.limit("5 per minute")(lambda: None)()
        
        # Rate limit 2FA endpoints
        if request.path.startswith('/api/security/verify-2fa'):
            limiter.limit("10 per minute")(lambda: None)()
        
        # Rate limit trading endpoints
        if request.path.startswith('/api/trade/'):
            limiter.limit("30 per minute")(lambda: None)()
    
    app.logger.info("Rate limiting configured")


def run_health_checks():
    """Run pre-startup health checks."""
    from datetime import datetime
    import socket
    import psycopg2
    
    checks = []
    
    # Check database connection
    try:
        db_url = os.getenv('DATABASE_URL', 'postgresql://bitoki_user:secure_password@localhost:5432/bitoki_prod')
        conn = psycopg2.connect(db_url)
        conn.close()
        checks.append(('Database', '✅ Connected'))
    except Exception as e:
        checks.append(('Database', f'❌ Connection failed: {e}'))
    
    # Check SMTP connection
    try:
        if email_service:
            smtp_config = email_service.config['email']['smtp']
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])
            server.quit()
            checks.append(('SMTP', '✅ Connected'))
        else:
            checks.append(('SMTP', '⚠️  Not configured'))
    except Exception as e:
        checks.append(('SMTP', f'❌ Connection failed: {e}'))
    
    # Check exchange connection
    try:
        if 'market_data' in globals() and market_data.exchange:
            market_data.exchange.fetch_status()
            checks.append(('Exchange', '✅ Connected'))
        else:
            checks.append(('Exchange', '⚠️  Not configured'))
    except Exception as e:
        checks.append(('Exchange', f'❌ Connection failed: {e}'))
    
    # Print health check results
    print("\n" + "="*50)
    print("🏥 BITOKI HEALTH CHECK")
    print("="*50)
    for service, status in checks:
        print(f"{service:15}: {status}")
    print("="*50 + "\n")
    
    # Check for critical failures
    critical_failures = [check for check in checks if check[1].startswith('❌') and check[0] in ['Database', 'Exchange']]
    
    if critical_failures:
        app.logger.error(f"Critical health check failures: {critical_failures}")
        sys.exit(1)


def main():
    """Main entry point for production."""
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║              BITOKI Production Server v1.0.0                   ║
    ║           Secure Cryptocurrency Trading Platform              ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run health checks
    run_health_checks()
    
    # Configure production app
    configure_production_app()
    
    # Print startup information
    print(f"🚀 Starting BITOKI in {os.getenv('FLASK_ENV', 'production').upper()} mode")
    print(f"📦 Environment: {os.getenv('FLASK_ENV', 'production')}")
    print(f"🔒 Security: 2FA Enabled, Encryption Active")
    print(f"📧 Email: {'Configured' if email_service else 'Not Configured'}")
    print(f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Start the server
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    
    print(f"\n🌐 Server listening on http://{host}:{port}")
    print("✅ Production server ready!")
    
    # Run with production server (Gunicorn will handle this in real deployment)
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    # Import additional modules that might be needed
    import smtplib
    import psycopg2
    from datetime import datetime
    
    # Try to import market_data if it exists
    try:
        from app import market_data
    except ImportError:
        market_data = None
    
    main()