# Quick Start Guide

Get BITfisher running in 5 minutes!

## For Live Trading (Real Money)

**⚠️ WARNING: This will trade with real money. You can lose all your capital.**

### 1. Install

```bash
# Windows
install.bat

# Linux/Mac
chmod +x install.sh
./install.sh
```

### 2. Configure API Credentials

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your exchange credentials:
```
EXCHANGE_API_KEY=your_binance_api_key
EXCHANGE_API_SECRET=your_binance_api_secret
TRADE_MODE=live
```

### 3. Adjust Risk Settings (Optional)

Edit `config/strategy_config.yaml` if you want to change:
- Risk per trade (default: 2%)
- Daily loss limit (default: 10%)
- Max concurrent trades (default: 3)

### 4. Run the Bot

```bash
uv run python run.py
```

Type `I UNDERSTAND THE RISKS` when prompted.

## For Testing (Dry Run - No Real Money)

### Quick Test Run

```bash
# 1. Install dependencies
uv pip install -e .

# 2. Set mode to dry_run in config/strategy_config.yaml
# Change: trade_mode: "live"
# To:     trade_mode: "dry_run"

# 3. Run
uv run python run.py
```

No API credentials needed for dry run mode!

## What Happens Next?

The bot will:
1. Connect to the exchange
2. Monitor BTC/USD on 1h and 2h timeframes
3. Check for high-impact news events
4. Detect chart patterns (H&S, Double Top, Rectangles)
5. Place trades when patterns are confirmed
6. Manage positions with stop loss and take profit

## Monitoring

Watch the console output or check logs:
```bash
tail -f logs/strategy.log
```

## Stop the Bot

Press `Ctrl+C` to stop gracefully.

## Need More Help?

- Detailed setup: See [SETUP.md](SETUP.md)
- Full documentation: See [README.md](README.md)
- Troubleshooting: Check the logs in `logs/strategy.log`

## Recommended First Steps

1. **Start with dry run** to observe behavior
2. **Test on sandbox/testnet** if your exchange supports it
3. **Use conservative risk settings** (1% per trade)
4. **Monitor regularly** - Don't leave it unattended
5. **Start small** - Only use capital you can afford to lose

## Important Safety Tips

- ✅ Always test in dry run mode first
- ✅ Start with small position sizes
- ✅ Monitor the bot daily
- ✅ Set appropriate daily loss limits
- ✅ Keep API credentials secure
- ❌ Never invest more than you can afford to lose
- ❌ Don't leave the bot running unattended for days
- ❌ Don't use your entire trading capital immediately

Good luck and trade safely! 🚀
