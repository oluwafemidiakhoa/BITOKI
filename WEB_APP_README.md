# BITOKI Web Application

A user-friendly web interface for the BITOKI cryptocurrency trading platform.

## Features

### 1. **Dashboard** 📊
- Portfolio overview with total balance
- Asset distribution pie chart
- Portfolio performance line chart
- Recent activity and transactions
- Real-time balance updates

### 2. **Cryptocurrency Trading** 💱
- **Buy Crypto**: Purchase BTC, ETH, SOL, USDT with multiple payment options
- **Sell Crypto**: Sell your cryptocurrencies for USDT, USD, or NGN
- **Swap**: Instantly swap between different cryptocurrencies
- Real-time price updates
- Order history tracking

### 3. **Multi-Currency Wallet** 👛
- Supported currencies:
  - Bitcoin (BTC)
  - Ethereum (ETH)
  - Solana (SOL)
  - Tether ERC20 (USDT)
  - Tether TRC20 (USDT)
  - Nigerian Naira (NGN)
- Deposit addresses for each currency
- Transaction history
- Send/Receive functionality

### 4. **Gift Card Trading** 🎁
- Trade popular gift cards:
  - Amazon, iTunes, Google Play
  - Steam, Xbox, PlayStation
  - Walmart, Target, eBay
  - Nike, Sephora, Nordstrom
  - And many more!
- Sell gift cards for crypto
- Buy gift cards with crypto
- Competitive rates (70-85%)
- Instant processing

### 5. **Crypto Savings** 🏦
- Earn interest on your crypto holdings
- Flexible savings (withdraw anytime):
  - Bitcoin: 5.0% APY
  - Ethereum: 6.5% APY
  - Solana: 8.0% APY
  - USDT: 10.0% APY
  - Naira: 15.0% APY
- Locked savings (up to 20% APY)
- Track earnings and growth

## Installation

### Prerequisites
- Python 3.10 or higher
- uv package manager
- Binance API key (or other supported exchange)

### Setup

1. **Install dependencies:**
   ```bash
   uv pip install -e .
   ```

2. **Configure API credentials:**

   Your API key is already set in `.env`:
   ```
   EXCHANGE_API_KEY=TgV9K6T6ir3OGiJ8RYg2OiYgKpYQxAP4X2tqFKwqQW1ZkMKAUTR3Ytpx7zwW5OAj
   EXCHANGE_API_SECRET=your_api_secret_here
   ```

   **⚠️ IMPORTANT:** Add your API secret!

3. **Run the web application:**
   ```bash
   python app.py
   ```

4. **Access the application:**

   Open your browser and go to: **http://localhost:5000**

## Quick Start

### For First-Time Users

1. **Start the web app:**
   ```bash
   python app.py
   ```

2. **Navigate to pages:**
   - **Dashboard**: http://localhost:5000/dashboard
   - **Wallet**: http://localhost:5000/wallet
   - **Trade**: http://localhost:5000/trade
   - **Savings**: http://localhost:5000/savings
   - **Gift Cards**: http://localhost:5000/giftcards

3. **Try out features:**
   - Check your wallet balances
   - Buy some crypto
   - View gift card rates
   - Start a savings plan

## Application Structure

```
BITOKI/
├── app.py                 # Main Flask application
├── web/
│   ├── templates/         # HTML templates
│   │   ├── base.html     # Base layout
│   │   ├── index.html    # Home page
│   │   ├── dashboard.html
│   │   ├── wallet.html
│   │   ├── trade.html
│   │   ├── savings.html
│   │   └── giftcards.html
│   └── static/           # Static assets
│       ├── css/
│       │   └── style.css  # Custom styles
│       └── js/
│           └── main.js    # JavaScript functions
├── api/                   # API modules
│   ├── wallet.py         # Wallet management
│   ├── trading.py        # Trading operations
│   └── giftcard.py       # Gift card API
└── src/bitoki/           # Trading bot backend
```

## API Endpoints

### Wallet APIs
- `GET /api/wallet/balances` - Get all wallet balances
- `GET /api/wallet/deposit-address/<currency>` - Get deposit address
- `GET /api/wallet/transactions` - Get transaction history

### Trading APIs
- `POST /api/trade/buy` - Buy cryptocurrency
- `POST /api/trade/sell` - Sell cryptocurrency
- `POST /api/trade/swap` - Swap cryptocurrencies
- `GET /api/trade/price/<currency>` - Get current price
- `GET /api/trade/history` - Get trade history

### Gift Card APIs
- `GET /api/giftcards/available` - Get available gift cards
- `POST /api/giftcards/sell` - Sell a gift card
- `POST /api/giftcards/buy` - Buy a gift card
- `POST /api/giftcards/calculate-payout` - Calculate payout
- `GET /api/giftcards/history` - Get trade history

## Usage Examples

### Buy Cryptocurrency
1. Go to **Trade** page
2. Click **Buy** tab
3. Select currency (BTC, ETH, SOL, USDT)
4. Enter amount
5. Choose payment method
6. Click "Buy Now"

### Sell Gift Card
1. Go to **Gift Cards** page
2. Find your gift card brand
3. Click "Sell"
4. Enter face value and card details
5. See payout estimate
6. Click "Sell Card"

### Start Savings
1. Go to **Savings** page
2. Choose a currency (BTC, ETH, SOL, USDT, NGN)
3. Click "Start Saving"
4. Enter amount
5. See estimated yearly interest
6. Confirm deposit

## Features in Detail

### Dashboard
- **Portfolio Value**: Total value of all assets in USD
- **Asset Charts**: Visual representation of portfolio
- **Recent Activity**: Latest transactions and trades
- **Performance Metrics**: Daily profit, win rate, open trades

### Wallet
- **Multi-Currency Support**: Store 6 different currencies
- **Deposit/Withdraw**: Easy fund management
- **Transaction History**: Track all movements
- **QR Codes**: For easy deposits (when available)

### Trading
- **Market Orders**: Instant execution at current price
- **Limit Orders**: Set your desired price
- **Swap Feature**: Direct crypto-to-crypto exchange
- **Price Charts**: Real-time price updates

### Gift Cards
- **12+ Brands**: Major retailers and platforms
- **Competitive Rates**: 70-85% of face value
- **Instant Processing**: Quick turnaround
- **Categories**: Shopping, Gaming, Entertainment, Fashion

### Savings
- **Flexible Plans**: Withdraw anytime
- **Locked Plans**: Higher APY for locked periods
- **Auto-Compound**: Interest automatically reinvested
- **Multiple Currencies**: Diversify your savings

## Security

### Best Practices
- ✅ API keys stored in `.env` file (never in code)
- ✅ Environment variables for sensitive data
- ✅ HTTPS recommended for production
- ✅ Input validation on all forms
- ✅ CORS protection enabled

### Recommendations
- Use API keys with minimal permissions
- Enable IP whitelist on exchange
- Use 2FA on exchange account
- Regularly monitor transactions
- Keep API secret secure

## Troubleshooting

### Port Already in Use
```bash
# Change port in app.py or kill process
lsof -ti:5000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :5000    # Windows
```

### API Connection Errors
- Check API key in `.env` file
- Verify API secret is set
- Ensure exchange API is accessible
- Check internet connection

### Template Not Found
- Ensure `web/templates/` directory exists
- Check file names match exactly
- Restart Flask application

### Static Files Not Loading
- Clear browser cache
- Check `web/static/` directory structure
- Verify file paths in templates

## Development Mode

To run in development mode with auto-reload:

```python
# In app.py, ensure debug=True
app.run(host='0.0.0.0', port=5000, debug=True)
```

## Production Deployment

For production, use a proper WSGI server:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Environment Variables

Required in `.env`:
```
EXCHANGE_API_KEY=your_api_key
EXCHANGE_API_SECRET=your_api_secret
TRADE_MODE=live
FLASK_SECRET_KEY=random_secret_key_here
```

## Browser Compatibility

Tested on:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Mobile Responsive

The application is fully responsive and works on:
- 📱 Smartphones (320px+)
- 📱 Tablets (768px+)
- 💻 Desktop (1024px+)

## Technologies Used

### Backend
- Flask 3.0 (Web framework)
- CCXT (Exchange connectivity)
- Pandas (Data processing)
- Python-dotenv (Environment management)

### Frontend
- Bootstrap 5.3 (UI framework)
- jQuery 3.6 (JavaScript library)
- Chart.js 4.4 (Charts and graphs)
- Font Awesome 6.4 (Icons)

## Support

For issues or questions:
1. Check logs in `logs/strategy.log`
2. Review error messages in browser console
3. Verify API credentials
4. Check exchange API status

## Future Enhancements

Planned features:
- [ ] User authentication & accounts
- [ ] Real-time WebSocket updates
- [ ] Advanced charting (TradingView)
- [ ] Mobile app (React Native)
- [ ] Push notifications
- [ ] Two-factor authentication
- [ ] KYC verification
- [ ] Referral program
- [ ] API rate limiting
- [ ] Trade analytics dashboard

## License

MIT License - See main README.md

## Disclaimer

**IMPORTANT**: This platform handles real money and cryptocurrency.

- Trading carries risk of loss
- Test thoroughly before live trading
- Keep API credentials secure
- Monitor trades regularly
- You are responsible for your trading decisions

---

**Happy Trading!** 🚀

For the automated trading bot documentation, see the main [README.md](README.md).
