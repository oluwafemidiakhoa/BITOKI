# 🌍 Binance API Setup for African Markets

## Step 1: Create Binance Account
1. Go to [Binance.com](https://www.binance.com)
2. Sign up with your email address
3. Complete KYC verification for your African country
4. Enable 2FA for security

## Step 2: Create API Keys
1. Login to your Binance account
2. Go to **Account** → **API Management**
3. Click **Create API**
4. Name it: `BITOKI Trading Bot`
5. **Enable these permissions:**
   - ✅ **Read Info** (to get balances)
   - ✅ **Spot & Margin Trading** (to execute trades)
   - ❌ **Futures Trading** (disable for safety)
   - ❌ **Margin Trading** (disable for safety)
   - ❌ **Withdrawals** (disable for maximum security)

## Step 3: Configure IP Restrictions (Recommended)
1. In API settings, add your current IP address
2. This prevents unauthorized access even if keys are compromised
3. You can find your IP at: [whatismyipaddress.com](https://whatismyipaddress.com)

## Step 4: Update Your .env File
Replace the values in your `.env` file:

```bash
# Replace with your actual Binance API credentials
EXCHANGE_API_KEY=your_actual_api_key_from_binance
EXCHANGE_API_SECRET=your_actual_api_secret_from_binance

# Make sure these are set correctly for Africa
TRADE_MODE=live
```

## Step 5: Test the Configuration
After updating your `.env` file:

1. **Restart the application:**
   ```bash
   # Stop current app (Ctrl+C)
   # Then restart:
   python app.py
   ```

2. **Check the logs for successful connection:**
   - Look for: `✅ Exchange initialized successfully`
   - Instead of: `⚠️ Warning: Could not initialize exchange`

3. **Test trading features:**
   - Go to: http://127.0.0.1:5000/trade
   - Try a small test trade
   - Check if real prices load instead of mock data

## 🔒 Security Best Practices

### ✅ DO:
- Keep API secret safe and never share it
- Use IP restrictions
- Start with small amounts for testing
- Disable withdrawal permissions
- Enable 2FA on Binance account

### ❌ DON'T:
- Enable futures or margin trading initially
- Allow withdrawals via API
- Share your API keys publicly
- Use the same keys for multiple applications

## 🌍 Popular African Countries on Binance
- 🇳🇬 Nigeria
- 🇿🇦 South Africa  
- 🇰🇪 Kenya
- 🇬🇭 Ghana
- 🇺🇬 Uganda
- 🇹🇿 Tanzania
- 🇪🇬 Egypt
- 🇲🇦 Morocco

## 💱 Recommended Trading Pairs for Africa
1. **BTC/USDT** - Most liquid, global standard
2. **ETH/USDT** - Second largest crypto
3. **BNB/USDT** - Binance native token (lower fees)
4. **USDT/BUSD** - Stablecoin trading

## 🚨 Troubleshooting

### Error: "Service unavailable from restricted location"
- **Solution**: Use VPN if your location is temporarily restricted
- **Alternative**: Try Binance.us or local African exchanges

### Error: "Invalid signature"
- **Solution**: Check your API secret is correct
- **Solution**: Ensure system time is synchronized

### Error: "IP not whitelisted"
- **Solution**: Add your current IP to Binance API restrictions
- **Solution**: Remove IP restrictions for testing (less secure)

### Mock data showing instead of real prices
- **Solution**: Check API keys are valid
- **Solution**: Ensure you have spot trading permissions
- **Solution**: Restart the application after updating .env

## 📞 Support
- **Binance Support**: https://www.binance.com/en/support
- **BITOKI Issues**: Check the application logs for detailed error messages

---
**Made for African crypto traders! 🚀**