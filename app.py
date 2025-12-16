"""Flask web application for BITOKI trading platform."""

import os
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import ccxt
from dotenv import load_dotenv

from api.wallet import WalletManager
from api.trading import TradingAPI
from api.giftcard import GiftCardAPI
from src.bitoki.config import Config
from src.bitoki.data.market_data import MarketDataFetcher
from src.bitoki.security.security_manager import SecurityManager

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Initialize components
try:
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

# Initialize security manager
security_manager = SecurityManager()

wallet_manager = WalletManager(exchange)
trading_api = TradingAPI(exchange) if exchange else None
giftcard_api = GiftCardAPI()


# Routes
@app.route('/')
def index():
    """Main dashboard."""
    return render_template('index.html')


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


if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Run the app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
