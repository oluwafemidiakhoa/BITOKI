"""Flask web application for BITOKI trading platform."""

import os
from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, current_user as _flask_current_user, login_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
import ccxt
from dotenv import load_dotenv

from models import db, bcrypt, User
# import models_passkey  # Import passkey models to register tables - temporarily disabled
from api.wallet import WalletManager
from api.trading import TradingAPI
from api.giftcard import GiftCardAPI
from auth import auth_bp
from routes.ngn_wallet import ngn_bp
from routes.passkey import passkey_bp
from src.bitoki.config import Config
from src.bitoki.data.market_data import MarketDataFetcher
from src.bitoki.security.security_manager import SecurityManager
from services.email_service import mail

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Configure database and extensions
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bitoki.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
bcrypt.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.zoho.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
mail.init_app(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login sessions."""
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


# Provide a safe anonymous user for templates
class _AnonymousUser:
    is_authenticated = False
    username = "Guest"
    kyc_level = 0
    kyc_status = "pending"


@app.context_processor
def inject_current_user():
    """Ensure templates always have a current_user object."""
    if _flask_current_user is not None:
        try:
            return {"current_user": _flask_current_user}
        except Exception:
            pass
    return {"current_user": _AnonymousUser()}

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(ngn_bp, url_prefix='/ngn')
app.register_blueprint(passkey_bp, url_prefix='/passkey')

# Initialize components with fallback handling
try:
    config = Config('config/strategy_config.yaml')
    market_data = MarketDataFetcher(
        exchange_name=config.exchange_name,
        api_key=config.api_key,
        api_secret=config.api_secret,
        sandbox=config.is_sandbox
    )
    exchange = market_data.exchange
    print("Exchange initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize exchange: {e}")
    print("Running in mock mode with sample data")
    exchange = None

# Initialize security manager
security_manager = SecurityManager()

# Initialize email service - using Flask-Mail in app_prod.py instead
email_service = None

# Initialize APIs with fallback to mock data
wallet_manager = WalletManager(exchange)
# Always initialize TradingAPI - it will handle mock data when exchange is None
trading_api = TradingAPI(exchange)
giftcard_api = GiftCardAPI()


# Routes
@app.route('/')
def index():
    """Main dashboard."""
    return render_template('index.html')


@app.route('/health')
def health():
    """Container/platform health check endpoint."""
    return jsonify({'status': 'ok'})


@app.route('/dashboard')
def dashboard():
    """Dashboard page."""
    return render_template('dashboard.html')


@app.route('/wallet')
def wallet():
    """Wallet management page."""
    return render_template('wallet.html')


@app.route('/trade')
def trade():
    """Trading page."""
    return render_template('trade.html')


@app.route('/giftcards')
def giftcards():
    """Gift cards page."""
    return render_template('giftcards.html')


@app.route('/savings')
def savings():
    """Savings page."""
    return render_template('savings.html')


@app.route('/about')
def about():
    """About BITOKI page."""
    return render_template('about.html')


@app.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html')


@app.route('/faq')
def faq():
    """FAQ page."""
    return render_template('faq.html')


@app.route('/settings')
@login_required
def settings():
    """Settings page."""
    return render_template('settings.html')


@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_password or not new_password or not confirm_password:
        flash('All fields are required', 'error')
        return redirect(url_for('settings'))
    
    if not _flask_current_user.check_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('settings'))
    
    _flask_current_user.set_password(new_password)
    db.session.commit()
    flash('Password changed successfully', 'success')
    return redirect(url_for('settings'))


@app.route('/update-preferences', methods=['POST'])
@login_required 
def update_preferences():
    """Update user preferences."""
    trading_mode = request.form.get('trading_mode')
    email_notifications = request.form.get('email_notifications') == 'on'
    
    # Update user preferences (you may want to add fields to User model)
    flash('Preferences updated successfully', 'success')
    return redirect(url_for('settings'))


@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account."""
    confirm_delete = request.form.get('confirm_delete')
    password_confirm = request.form.get('password_confirm')
    
    if confirm_delete != 'DELETE':
        flash('Please type DELETE to confirm account deletion', 'error')
        return redirect(url_for('settings'))
    
    if not _flask_current_user.check_password(password_confirm):
        flash('Incorrect password', 'error')  
        return redirect(url_for('settings'))
    
    # Delete user account
    user_id = _flask_current_user.id
    db.session.delete(_flask_current_user)
    db.session.commit()
    
    flash('Account deleted successfully', 'info')
    return redirect(url_for('auth.login'))


@app.route('/terms')
def terms():
    """Terms of Service page."""
    return render_template('legal/terms.html')


@app.route('/privacy')
def privacy():
    """Privacy Policy page."""
    return render_template('legal/privacy.html')


@app.route('/kyc/verify')
def kyc_verify():
    """KYC verification page."""
    return render_template('kyc/verify.html')


@app.route('/api/kyc/submit', methods=['POST'])
def kyc_submit():
    """Handle KYC submission (stub)."""
    return jsonify({'success': True, 'message': 'KYC submitted for review'}), 200


@app.route('/api/kyc/documents', methods=['GET'])
def kyc_documents():
    """Return uploaded KYC documents (stub)."""
    return jsonify({'success': True, 'documents': []}), 200


# API Endpoints
@app.route('/api/wallet/balances', methods=['GET'])
def get_balances():
    """Get wallet balances."""
    try:
        balances = wallet_manager.get_balances()
        total = wallet_manager.get_total_balance_usd()

        return jsonify({
            'success': True,
            'balances': [b.__dict__ for b in balances],
            'total_usd': total
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/wallet/deposit-address/<currency>', methods=['GET'])
def get_deposit_address(currency):
    """Get deposit address for currency."""
    try:
        address = wallet_manager.generate_deposit_address(currency)
        return jsonify({'success': True, 'address': address})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/wallet/transactions', methods=['GET'])
def get_transactions():
    """Get transaction history."""
    try:
        currency = request.args.get('currency')
        limit = int(request.args.get('limit', 50))

        transactions = wallet_manager.get_transaction_history(currency, limit)
        return jsonify({'success': True, 'transactions': transactions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trade/buy', methods=['POST'])
def buy_crypto():
    """Buy cryptocurrency."""
    try:
        data = request.json
        currency = data.get('currency')
        amount = float(data.get('amount'))
        payment_currency = data.get('payment_currency', 'USDT')

        if not trading_api:
            return jsonify({'success': False, 'error': 'Trading API not initialized'}), 503

        order = trading_api.buy_crypto(currency, amount, payment_currency)

        return jsonify({
            'success': True,
            'order': order.__dict__
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trade/sell', methods=['POST'])
def sell_crypto():
    """Sell cryptocurrency."""
    try:
        data = request.json
        currency = data.get('currency')
        amount = float(data.get('amount'))
        receive_currency = data.get('receive_currency', 'USDT')

        if not trading_api:
            return jsonify({'success': False, 'error': 'Trading API not initialized'}), 503

        order = trading_api.sell_crypto(currency, amount, receive_currency)

        return jsonify({
            'success': True,
            'order': order.__dict__
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trade/swap', methods=['POST'])
def swap_crypto():
    """Swap cryptocurrency."""
    try:
        data = request.json
        from_currency = data.get('from_currency')
        to_currency = data.get('to_currency')
        amount = float(data.get('amount'))

        if not trading_api:
            return jsonify({'success': False, 'error': 'Trading API not initialized'}), 503

        order = trading_api.swap_crypto(from_currency, to_currency, amount)

        return jsonify({
            'success': True,
            'order': order.__dict__
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trade/price/<currency>', methods=['GET'])
def get_price(currency):
    """Get current price."""
    try:
        quote_currency = request.args.get('quote', 'USDT')

        if not trading_api:
            return jsonify({'success': False, 'error': 'Trading API not initialized'}), 503

        price = trading_api.get_price(currency, quote_currency)

        return jsonify({
            'success': True,
            'currency': currency,
            'quote_currency': quote_currency,
            'price': price
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trade/market-overview', methods=['GET'])
def market_overview():
    """Get market data for common currencies."""
    try:
        currencies = request.args.get('currencies', 'BTC,ETH,SOL,USDT').split(',')
        quote_currency = request.args.get('quote', 'USDT')

        if not trading_api:
            return jsonify({'success': False, 'error': 'Trading API not initialized'}), 503

        markets = []
        for currency in currencies:
            data = trading_api.get_market_data(currency, quote_currency)
            markets.append(data)

        return jsonify({'success': True, 'markets': markets})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trade/history', methods=['GET'])
def get_trade_history():
    """Get trade history."""
    try:
        limit = int(request.args.get('limit', 20))

        if not trading_api:
            return jsonify({'success': False, 'error': 'Trading API not initialized'}), 503

        trades = trading_api.get_recent_trades(limit)

        return jsonify({
            'success': True,
            'trades': trades
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/giftcards/available', methods=['GET'])
def get_available_giftcards():
    """Get available gift cards."""
    try:
        category = request.args.get('category')
        cards = giftcard_api.get_available_cards(category)

        return jsonify({
            'success': True,
            'cards': [c.__dict__ for c in cards]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/giftcards/categories', methods=['GET'])
def get_giftcard_categories():
    """Get gift card categories."""
    try:
        categories = giftcard_api.get_categories()
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/giftcards/sell', methods=['POST'])
def sell_giftcard():
    """Sell a gift card."""
    try:
        data = request.json
        card_id = data.get('card_id')
        code = data.get('code')
        pin = data.get('pin')
        face_value = data.get('face_value')

        trade = giftcard_api.sell_gift_card(card_id, code, pin, face_value)

        return jsonify({
            'success': True,
            'trade': trade.__dict__
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/giftcards/buy', methods=['POST'])
def buy_giftcard():
    """Buy a gift card."""
    try:
        data = request.json
        card_id = data.get('card_id')
        face_value = float(data.get('face_value'))
        payment_method = data.get('payment_method', 'crypto')

        trade = giftcard_api.buy_gift_card(card_id, face_value, payment_method)

        return jsonify({
            'success': True,
            'trade': trade.__dict__
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/giftcards/calculate-payout', methods=['POST'])
def calculate_giftcard_payout():
    """Calculate gift card payout."""
    try:
        data = request.json
        card_id = data.get('card_id')
        face_value = float(data.get('face_value'))

        payout = giftcard_api.calculate_payout(card_id, face_value)

        return jsonify({
            'success': True,
            'payout': payout
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/giftcards/history', methods=['GET'])
def get_giftcard_history():
    """Get gift card trade history."""
    try:
        limit = int(request.args.get('limit', 50))
        history = giftcard_api.get_trade_history(limit)

        return jsonify({
            'success': True,
            'history': [h.__dict__ for h in history]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Security Endpoints
@app.route('/api/security/setup-2fa', methods=['POST'])
def setup_2fa():
    """Set up two-factor authentication."""
    try:
        data = request.json
        user_id = data.get('user_id')
        method = data.get('method', 'totp')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User ID required'}), 400
        
        # Setup 2FA
        two_factor = security_manager.setup_2fa(user_id, method)
        
        # Generate QR code URL for TOTP
        if method == 'totp':
            issuer = "BITOKI"
            qr_code_url = f"https://chart.googleapis.com/chart?chs=200x200&chld=M|0&cht=qr&chl=otpauth://totp/{issuer}:{user_id}?secret={two_factor.secret}&issuer={issuer}"
        else:
            qr_code_url = ""
        
        # Send email with backup codes
        if email_service:
            email_service.send_2fa_setup_email(
                user_email=f"{user_id}@bitoki.com",  # In production, use real email
                qr_code_url=qr_code_url,
                backup_codes=two_factor.backup_codes
            )
        
        return jsonify({
            'success': True,
            'secret': two_factor.secret,
            'qr_code_url': qr_code_url,
            'backup_codes': two_factor.backup_codes,
            'method': two_factor.method
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/verify-2fa', methods=['POST'])
def verify_2fa():
    """Verify 2FA code."""
    try:
        data = request.json
        user_id = data.get('user_id')
        code = data.get('code')
        
        if not user_id or not code:
            return jsonify({'success': False, 'error': 'User ID and code required'}), 400
        
        is_valid = security_manager.verify_2fa_code(user_id, code)
        
        if is_valid:
            # Create security alert for successful 2FA verification
            security_manager.create_alert(
                user_id=user_id,
                alert_type='login',
                message=f'Successful 2FA verification from IP: {request.remote_addr}',
                severity='low'
            )
        
        return jsonify({
            'success': True,
            'is_valid': is_valid
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/alerts', methods=['GET'])
def get_security_alerts():
    """Get security alerts for a user."""
    try:
        user_id = request.args.get('user_id')
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User ID required'}), 400
        
        alerts = security_manager.get_alerts(user_id, unread_only)
        
        return jsonify({
            'success': True,
            'alerts': [{
                'alert_id': a.alert_id,
                'alert_type': a.alert_type,
                'message': a.message,
                'timestamp': a.timestamp,
                'is_read': a.is_read,
                'severity': a.severity
            } for a in alerts]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/mark-alert-read', methods=['POST'])
def mark_alert_read():
    """Mark a security alert as read."""
    try:
        data = request.json
        user_id = data.get('user_id')
        alert_id = data.get('alert_id')
        
        if not user_id or not alert_id:
            return jsonify({'success': False, 'error': 'User ID and alert ID required'}), 400
        
        success = security_manager.mark_alert_as_read(user_id, alert_id)
        
        return jsonify({
            'success': success
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/transaction-history', methods=['GET'])
def get_transaction_history():
    """Get immutable transaction history."""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User ID required'}), 400
        
        transactions = security_manager.get_transaction_history(user_id)
        chain_valid = security_manager.verify_transaction_chain()
        
        return jsonify({
            'success': True,
            'transactions': [{
                'transaction_id': t.transaction_id,
                'type': t.type,
                'amount': t.amount,
                'currency': t.currency,
                'timestamp': t.timestamp,
                'status': t.status,
                'verified': chain_valid
            } for t in transactions],
            'chain_valid': chain_valid
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/check-fraud', methods=['POST'])
def check_fraud():
    """Check transaction for fraud patterns."""
    try:
        data = request.json
        
        is_fraudulent, reason = security_manager.check_fraud_patterns(data)
        
        return jsonify({
            'success': True,
            'is_fraudulent': is_fraudulent,
            'reason': reason
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/security/test-email', methods=['POST'])
def test_email():
    """Test email sending."""
    try:
        if not email_service:
            return jsonify({'success': False, 'error': 'Email service not available'}), 500
        
        data = request.json
        email = data.get('email', 'test@example.com')
        
        success = email_service.send_test_email(email)
        
        return jsonify({
            'success': success,
            'message': 'Test email sent' if success else 'Failed to send test email'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    debug_flag = str(os.getenv('FLASK_DEBUG', '0')).lower() in ('1', 'true', 'yes')
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))

    # Run the app
    app.run(
        host=host,
        port=port,
        debug=debug_flag
    )
