# BITOKI Setup Guide

This guide will walk you through setting up the BITOKI trading bot for live trading.

## Prerequisites

1. **Python 3.10 or higher** installed on your system
2. **uv package manager** installed:
   ```bash
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Exchange Account** with API access:
   - Binance (recommended) or another CCXT-supported exchange
   - Enable API key with trading permissions
   - If available, use testnet/sandbox for initial testing

## Step-by-Step Setup

### 1. Install Dependencies

Navigate to the project directory and install dependencies using uv:

```bash
cd c:\Users\adminidiakhoa\Demo\BITOKI
uv pip install -e .
```

### 2. Configure API Credentials

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your exchange credentials:
   ```
   EXCHANGE_API_KEY=your_actual_api_key_here
   EXCHANGE_API_SECRET=your_actual_api_secret_here
   TRADE_MODE=dry_run
   ```

   **Security Note**: Never commit the `.env` file to version control!

### 3. Configure Strategy Settings

Edit `config/strategy_config.yaml`:

```yaml
# For real trading, update these settings:
trade_mode: "live"        # Change from "dry_run" to "live"

exchange:
  name: "binance"         # Your exchange
  sandbox: false          # Set to false for real trading

# Adjust risk parameters as needed:
risk_pct: 0.02           # 2% risk per trade
max_concurrent_trades: 3
daily_loss_limit_pct: 0.10  # 10% daily loss limit
```

### 4. Test in Dry Run Mode First

**IMPORTANT**: Always test in dry run mode before live trading!

```bash
uv run python run.py
```

Let it run for several hours or days to observe:
- Pattern detection accuracy
- Entry/exit logic
- Risk management behavior
- Any errors or issues

### 5. Enable Live Trading

When you're confident the bot works correctly:

1. **Option A**: Update `config/strategy_config.yaml`:
   ```yaml
   trade_mode: "live"
   exchange:
     sandbox: false
   ```

2. **Option B**: Update `.env` file:
   ```
   TRADE_MODE=live
   ```

3. Run the bot:
   ```bash
   uv run python run.py
   ```

4. You'll see a warning message. Type `I UNDERSTAND THE RISKS` to proceed.

### 6. Monitor Your Bot

- Watch the console output for real-time activity
- Check logs in `logs/strategy.log`
- Monitor your exchange account regularly
- Set up alerts for critical events (optional)

## Exchange-Specific Setup

### Binance

1. Go to https://www.binance.com/en/my/settings/api-management
2. Create a new API key
3. Enable "Enable Spot & Margin Trading"
4. Restrict to your IP address (recommended)
5. Copy API Key and Secret Key to `.env`

For testnet:
```yaml
exchange:
  name: "binance"
  sandbox: true
```
Use testnet API credentials from https://testnet.binance.vision/

### Bybit

```yaml
exchange:
  name: "bybit"
  sandbox: false  # or true for testnet
```

### Kraken

```yaml
exchange:
  name: "kraken"
  sandbox: false
```

## Recommended First-Time Settings

For your first live run, use conservative settings:

```yaml
risk_pct: 0.01              # 1% per trade (instead of 2%)
max_concurrent_trades: 1     # Start with 1 trade at a time
max_trades_per_day: 3        # Limit daily trades
daily_loss_limit_pct: 0.05   # 5% daily loss limit
```

## Monitoring and Maintenance

### View Live Logs

```bash
# Follow logs in real-time
tail -f logs/strategy.log
```

### Check Statistics

The bot prints statistics at each iteration showing:
- Open trades
- Daily trades and PnL
- Win rate
- Total PnL

### Emergency Stop

Press `Ctrl+C` to gracefully stop the bot. It will:
- Stop opening new positions
- Leave existing positions open (you must close them manually if desired)

## Troubleshooting

### "Insufficient funds"

- Check your exchange account balance
- Reduce position size or risk percentage
- Ensure you have margin available (for futures trading)

### "Invalid API credentials"

- Verify API key and secret in `.env`
- Check API permissions on exchange
- Ensure IP whitelist includes your current IP

### "Rate limit exceeded"

- The bot uses `enableRateLimit: True` but you might still hit limits
- Increase `poll_interval_seconds` in config
- Contact exchange support for higher rate limits

### No patterns detected

- Patterns are relatively rare - be patient
- Markets need sufficient volatility
- Adjust `min_pattern_bars` or `symmetry_tolerance` in code

## Safety Checklist

Before going live:

- [ ] Tested in dry run mode for at least 24-48 hours
- [ ] API credentials are secured (not in code, only in `.env`)
- [ ] Risk parameters are conservative
- [ ] Daily loss limit is set appropriately
- [ ] You understand all patterns and entry/exit rules
- [ ] You can monitor the bot regularly
- [ ] You have tested emergency stop (Ctrl+C)
- [ ] Exchange account has only trading capital (not life savings)
- [ ] You understand you may lose all invested capital

## Getting Help

If you encounter issues:

1. Check the logs in `logs/strategy.log`
2. Review this setup guide
3. Check the main README.md
4. Ensure your exchange API has correct permissions
5. Test with smaller position sizes first

## Important Reminders

- **Never invest more than you can afford to lose**
- **Cryptocurrency trading is highly risky**
- **Monitor your bot daily**
- **Start with small amounts**
- **Keep API credentials secure**
- **The bot is not guaranteed to be profitable**
- **You are responsible for your own trading decisions**

Happy (safe) trading! 🚀
