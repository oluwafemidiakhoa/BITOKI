# 🚀 START HERE - BITfisher Trading Bot

Welcome! This guide will get you up and running with the BITfisher BTC/USD automated trading bot.

## What You've Built

A complete automated trading system that:
- ✅ Detects 5 chart patterns (H&S, Double Top, Rectangles)
- ✅ Manages risk with 2% position sizing
- ✅ Filters trades during high-impact news
- ✅ Executes trades with stop loss and take profit
- ✅ Tracks statistics and enforces daily limits
- ✅ Supports both dry run (testing) and live trading

## ⚡ Quick Start (5 Minutes)

### Step 1: Install Dependencies

**Windows:**
```bash
install.bat
```

**Linux/Mac:**
```bash
chmod +x install.sh
./install.sh
```

Or manually:
```bash
uv pip install -e .
```

### Step 2: Verify Setup

```bash
uv run python verify_setup.py
```

This will check if everything is configured correctly.

### Step 3: Configure API Credentials

**For Live Trading:**
```bash
# Create .env file
cp .env.example .env

# Edit .env and add your Binance API credentials
# EXCHANGE_API_KEY=your_actual_key
# EXCHANGE_API_SECRET=your_actual_secret
```

**For Testing (Dry Run):**
No credentials needed! Skip this step.

### Step 4: Choose Trading Mode

Edit [config/strategy_config.yaml](config/strategy_config.yaml):

**For Testing (Recommended First):**
```yaml
trade_mode: "dry_run"
exchange:
  sandbox: true
```

**For Live Trading:**
```yaml
trade_mode: "live"
exchange:
  sandbox: false  # CAREFUL: Real money!
```

### Step 5: Run the Bot

```bash
uv run python run.py
```

For live trading, you'll need to type `I UNDERSTAND THE RISKS` to proceed.

## 📊 What to Expect

Once running, you'll see:
```
🚀 Starting trading strategy...

=== Iteration 1 ===
Processing 1h timeframe...
Trend: bullish (strength: 0.65)
Detected 2 pattern(s): ['InvertedHnS', 'ErectRect']
✅ Pattern InvertedHnS confirmed with retest!
Placing buy order...

📊 Statistics:
  Open trades: 1
  Today's trades: 1
  Today's PnL: $0.00
  ...

Sleeping for 60 seconds...
```

The bot will:
1. Check market data every 60 seconds
2. Look for patterns on 1h and 2h timeframes
3. Verify news events
4. Execute trades when patterns confirm
5. Track all positions and PnL

## 🛑 Stop the Bot

Press `Ctrl+C` to stop gracefully.

**Note:** This stops opening new trades. Existing positions remain open - close them manually on your exchange if needed.

## 📁 Important Files

| File | Purpose |
|------|---------|
| [run.py](run.py) | Main entry point - run this |
| [config/strategy_config.yaml](config/strategy_config.yaml) | All strategy settings |
| [.env](.env) | API credentials (create from .env.example) |
| [logs/strategy.log](logs/) | Detailed logs (created when running) |
| [README.md](README.md) | Full documentation |
| [SETUP.md](SETUP.md) | Detailed setup guide |
| [QUICKSTART.md](QUICKSTART.md) | Quick reference guide |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Technical architecture |

## ⚙️ Key Configuration Options

In [config/strategy_config.yaml](config/strategy_config.yaml):

```yaml
# What to trade
symbol: "BTC/USD"
timeframes: ["1h", "2h"]

# Which patterns to use
allowed_patterns:
  - ErectHnS
  - InvertedHnS
  - DoubleTop
  - ErectRect
  - InvRect

# Risk per trade (2% = 0.02)
risk_pct: 0.02

# Take profit target in USD
take_profit_pips: 200

# Maximum open trades at once
max_concurrent_trades: 3

# Maximum daily loss (10% = 0.10)
daily_loss_limit_pct: 0.10

# Trading mode
trade_mode: "live"  # or "dry_run"

# Exchange
exchange:
  name: "binance"
  sandbox: false
```

## 🔍 Monitoring

### View Logs in Real-Time
```bash
tail -f logs/strategy.log
```

### Check Statistics
Statistics are printed every iteration showing:
- Open trades
- Daily PnL
- Win rate
- Total trades

### Exchange Account
Monitor your exchange account regularly to:
- Verify orders are placed correctly
- Check balances
- Close positions manually if needed

## ⚠️ Safety Checklist

Before going live:

- [ ] Tested in dry_run mode for at least 24 hours
- [ ] Verified pattern detection works as expected
- [ ] Confirmed risk settings are appropriate
- [ ] Set up API keys with correct permissions (no withdrawals!)
- [ ] IP whitelisted API keys on exchange
- [ ] Started with small test amount
- [ ] Understand how to stop the bot (Ctrl+C)
- [ ] Can monitor the bot regularly
- [ ] Read and understood all warnings in README.md

## 🎯 Recommended First-Time Settings

Start conservative:

```yaml
risk_pct: 0.01              # 1% per trade
max_concurrent_trades: 1     # Only 1 trade at a time
max_trades_per_day: 3        # Max 3 trades per day
daily_loss_limit_pct: 0.05   # 5% daily loss limit
```

## 🆘 Troubleshooting

### "Config file not found"
```bash
# Check that config/strategy_config.yaml exists
ls config/
```

### "API credentials not configured"
```bash
# Make sure .env exists and has your keys
cat .env
```

### "Module not found"
```bash
# Reinstall dependencies
uv pip install -e .
```

### "No patterns detected"
- This is normal - patterns are relatively rare
- Wait for market volatility
- Patterns may take hours/days to form

### "Insufficient funds"
- Check exchange balance
- Reduce risk_pct or position sizes
- Ensure you have margin (for futures)

## 📚 Learn More

- **Architecture & Code:** See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- **Detailed Setup:** See [SETUP.md](SETUP.md)
- **Full Docs:** See [README.md](README.md)
- **Quick Reference:** See [QUICKSTART.md](QUICKSTART.md)

## 🚨 Critical Warnings

### For Live Trading

**⚠️ YOU CAN LOSE ALL YOUR MONEY**

- Cryptocurrency trading is extremely risky
- This bot is provided AS-IS with no guarantees
- Past performance does not predict future results
- The developers are NOT responsible for any losses
- Never invest more than you can afford to lose
- Always monitor your bot - don't leave it unattended
- Start with small amounts to test
- Set appropriate risk limits

### Security

- Never share your `.env` file
- Use API keys with minimal permissions (trading only, no withdrawals)
- Enable IP whitelist on your exchange API keys
- Keep your API credentials secure
- Don't commit `.env` to git (already in .gitignore)

## ✅ You're Ready!

If you've completed the 5 steps above and checked the safety list, you're ready to trade!

**For Testing:**
```bash
# Set trade_mode: "dry_run" in config
uv run python run.py
```

**For Live Trading:**
```bash
# Set trade_mode: "live" in config
# Add API credentials to .env
uv run python run.py
# Type: I UNDERSTAND THE RISKS
```

## 💬 Need Help?

1. Check the logs: `logs/strategy.log`
2. Run verification: `uv run python verify_setup.py`
3. Review documentation in this folder
4. Check exchange API documentation
5. Test in dry run mode first

---

**Good luck and trade safely!** 🚀📈

Remember: The best traders are patient, disciplined, and manage risk carefully. This bot is a tool to help you - use it wisely.
