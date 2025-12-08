"""Production-ready Flask application for BITOKI with authentication."""

import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models and setup database
from models import db, bcrypt, User
from auth import auth_bp

# Import existing APIs
from api.wallet import WalletManager
from api.trading import TradingAPI
from api.giftcard import GiftCardAPI

# Create Flask app
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bitoki.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
CORS(app)

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please login to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

# Initialize trading components
try:
    from src.bitoki.config import Config
    from src.bitoki.data.market_data import MarketDataFetcher

    config = Config('config/strategy_config.yaml')
    market_data = MarketDataFetcher(
        exchange_name=config.exchange_name,
        api_key=config.api_key,
        api_secret=config.api_secret,
        sandbox=config.is_sandbox
    )
    exchange = market_data.exchange
except Exception as e:
    print(f"Warning: Could not initialize exchange: {e}")
    exchange = None

wallet_manager = WalletManager(exchange)
trading_api = TradingAPI(exchange) if exchange else None
giftcard_api = GiftCardAPI()

# Routes
@app.route('/')
def index():
    """Home page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page - requires login."""
    return render_template('dashboard.html')

@app.route('/wallet')
@login_required
def wallet():
    """Wallet page - requires login."""
    return render_template('wallet.html')

@app.route('/trade')
@login_required
def trade():
    """Trading page - requires login."""
    return render_template('trade.html')

@app.route('/giftcards')
@login_required
def giftcards():
    """Gift cards page - requires login."""
    return render_template('giftcards.html')

@app.route('/savings')
@login_required
def savings():
    """Savings page - requires login."""
    return render_template('savings.html')

@app.route('/settings')
@login_required
def settings():
    """User settings page."""
    return render_template('settings.html')

# API Endpoints (existing from app.py)
from flask import jsonify, request

@app.route('/api/wallet/balances', methods=['GET'])
@login_required
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
@login_required
def get_deposit_address(currency):
    """Get deposit address for currency."""
    try:
        address = wallet_manager.generate_deposit_address(currency)
        return jsonify({'success': True, 'address': address})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/wallet/transactions', methods=['GET'])
@login_required
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
@login_required
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
        return jsonify({'success': True, 'order': order.__dict__})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trade/sell', methods=['POST'])
@login_required
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
        return jsonify({'success': True, 'order': order.__dict__})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trade/swap', methods=['POST'])
@login_required
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
        return jsonify({'success': True, 'order': order.__dict__})
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

@app.route('/api/trade/history', methods=['GET'])
@login_required
def get_trade_history():
    """Get trade history."""
    try:
        limit = int(request.args.get('limit', 20))
        if not trading_api:
            return jsonify({'success': False, 'error': 'Trading API not initialized'}), 503

        trades = trading_api.get_recent_trades(limit)
        return jsonify({'success': True, 'trades': trades})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/giftcards/available', methods=['GET'])
def get_available_giftcards():
    """Get available gift cards."""
    try:
        category = request.args.get('category')
        cards = giftcard_api.get_available_cards(category)
        return jsonify({'success': True, 'cards': [c.__dict__ for c in cards]})
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
@login_required
def sell_giftcard():
    """Sell a gift card."""
    try:
        data = request.json
        trade = giftcard_api.sell_gift_card(
            data.get('card_id'),
            data.get('code'),
            data.get('pin'),
            data.get('face_value')
        )
        return jsonify({'success': True, 'trade': trade.__dict__})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/giftcards/buy', methods=['POST'])
@login_required
def buy_giftcard():
    """Buy a gift card."""
    try:
        data = request.json
        trade = giftcard_api.buy_gift_card(
            data.get('card_id'),
            float(data.get('face_value')),
            data.get('payment_method', 'crypto')
        )
        return jsonify({'success': True, 'trade': trade.__dict__})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/giftcards/calculate-payout', methods=['POST'])
def calculate_giftcard_payout():
    """Calculate gift card payout."""
    try:
        data = request.json
        payout = giftcard_api.calculate_payout(
            data.get('card_id'),
            float(data.get('face_value'))
        )
        return jsonify({'success': True, 'payout': payout})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/giftcards/history', methods=['GET'])
@login_required
def get_giftcard_history():
    """Get gift card trade history."""
    try:
        limit = int(request.args.get('limit', 50))
        history = giftcard_api.get_trade_history(limit)
        return jsonify({'success': True, 'history': [h.__dict__ for h in history]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Create logs directory
    os.makedirs('logs', exist_ok=True)

    # Run the app
    print("\n" + "="*60)
    print("BITOKI Exchange - Production Mode")
    print("="*60)
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Exchange: {config.exchange_name if exchange else 'Not configured'}")
    print(f"Trade Mode: {os.getenv('TRADE_MODE', 'live')}")
    print("="*60)
    print("\nServer starting at: http://127.0.0.1:5000")
    print("Network access at: http://10.234.10.77:5000")
    print("\nProduction mode - User authentication required")
    print("="*60 + "\n")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
