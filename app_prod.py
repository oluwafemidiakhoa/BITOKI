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

# Legal pages (public access)
@app.route('/terms')
def terms_of_service():
    """Terms of Service page."""
    return render_template('legal/terms.html')

@app.route('/privacy')
def privacy_policy():
    """Privacy Policy page."""
    return render_template('legal/privacy.html')

@app.route('/about')
def about_us():
    """About Us / Company Info page."""
    return render_template('legal/about.html')

@app.route('/fees')
def fee_schedule():
    """Fee Schedule page."""
    return render_template('legal/fees.html')

# Help pages
@app.route('/help/faq')
def faq():
    """FAQ page."""
    return render_template('help/faq.html')

# KYC pages
@app.route('/kyc/verify')
@login_required
def kyc_verify():
    """KYC verification page."""
    return render_template('kyc/verify.html')

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

@app.route('/api/wallet/balance/<currency>', methods=['GET'])
@login_required
def get_currency_balance(currency):
    """Get balance for a specific currency."""
    try:
        balance = wallet_manager.get_balance_for_currency(currency)
        return jsonify({
            'success': True,
            'currency': currency,
            'balance': balance
        })
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

        # Get current price to calculate total cost
        price = trading_api.get_price(currency, payment_currency)
        subtotal = amount * price
        fee = subtotal * 0.005  # 0.5% trading fee
        total_cost = subtotal + fee

        # Check balance before executing trade
        available_balance = wallet_manager.get_balance_for_currency(payment_currency)
        if available_balance < total_cost:
            return jsonify({
                'success': False,
                'error': f'Insufficient {payment_currency} balance. Available: {available_balance:.6f}, Required: {total_cost:.6f}'
            }), 400

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

        # Check balance before executing trade
        available_balance = wallet_manager.get_balance_for_currency(currency)
        if available_balance < amount:
            return jsonify({
                'success': False,
                'error': f'Insufficient {currency} balance. Available: {available_balance:.6f}, Required: {amount:.6f}'
            }), 400

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

        # Check balance before executing trade
        available_balance = wallet_manager.get_balance_for_currency(from_currency)
        if available_balance < amount:
            return jsonify({
                'success': False,
                'error': f'Insufficient {from_currency} balance. Available: {available_balance:.6f}, Required: {amount:.6f}'
            }), 400

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

@app.route('/api/trade/market-data/<currency>', methods=['GET'])
def get_market_data(currency):
    """Get market data with 24h change."""
    try:
        quote_currency = request.args.get('quote', 'USDT')
        if not trading_api:
            return jsonify({'success': False, 'error': 'Trading API not initialized'}), 503

        data = trading_api.get_market_data(currency, quote_currency)
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trade/market-overview', methods=['GET'])
def get_market_overview():
    """Get market overview for all supported currencies."""
    try:
        if not trading_api:
            return jsonify({'success': False, 'error': 'Trading API not initialized'}), 503

        currencies = ['BTC', 'ETH', 'SOL', 'USDT']
        overview = []

        for currency in currencies:
            data = trading_api.get_market_data(currency, 'USD')
            overview.append(data)

        return jsonify({
            'success': True,
            'markets': overview
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

# KYC API Endpoints
@app.route('/api/kyc/documents', methods=['GET'])
@login_required
def get_kyc_documents():
    """Get user's submitted KYC documents."""
    try:
        from models import KYCDocument
        documents = KYCDocument.query.filter_by(user_id=current_user.id).order_by(KYCDocument.created_at.desc()).all()

        docs_list = []
        for doc in documents:
            docs_list.append({
                'id': doc.id,
                'document_type': doc.document_type,
                'document_number': doc.document_number,
                'status': doc.status,
                'rejection_reason': doc.rejection_reason,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'verified_at': doc.verified_at.isoformat() if doc.verified_at else None
            })

        return jsonify({'success': True, 'documents': docs_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kyc/submit', methods=['POST'])
@login_required
def submit_kyc_document():
    """Submit KYC document for verification."""
    try:
        from models import KYCDocument
        from werkzeug.utils import secure_filename
        import uuid

        # Get form data
        document_type = request.form.get('document_type')
        document_number = request.form.get('document_number')

        if not document_type or not document_number:
            return jsonify({'success': False, 'error': 'Document type and number are required'}), 400

        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(os.getcwd(), 'uploads', 'kyc', str(current_user.id))
        os.makedirs(upload_dir, exist_ok=True)

        # Save uploaded files
        front_image_path = None
        back_image_path = None
        selfie_image_path = None

        if 'front_image' in request.files:
            front_file = request.files['front_image']
            if front_file.filename:
                filename = f"{uuid.uuid4()}_{secure_filename(front_file.filename)}"
                front_image_path = os.path.join(upload_dir, filename)
                front_file.save(front_image_path)

        if 'back_image' in request.files:
            back_file = request.files['back_image']
            if back_file.filename:
                filename = f"{uuid.uuid4()}_{secure_filename(back_file.filename)}"
                back_image_path = os.path.join(upload_dir, filename)
                back_file.save(back_image_path)

        if 'selfie_image' in request.files:
            selfie_file = request.files['selfie_image']
            if selfie_file.filename:
                filename = f"{uuid.uuid4()}_{secure_filename(selfie_file.filename)}"
                selfie_image_path = os.path.join(upload_dir, filename)
                selfie_file.save(selfie_image_path)

        # Create KYC document record
        kyc_doc = KYCDocument(
            user_id=current_user.id,
            document_type=document_type,
            document_number=document_number,
            front_image=front_image_path,
            back_image=back_image_path,
            selfie_image=selfie_image_path,
            status='pending'
        )

        db.session.add(kyc_doc)

        # Update user KYC status to pending
        current_user.kyc_status = 'pending'

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'KYC documents submitted successfully',
            'document_id': kyc_doc.id
        })
    except Exception as e:
        db.session.rollback()
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
