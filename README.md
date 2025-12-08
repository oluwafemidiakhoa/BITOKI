# BITOKI - BTC/USD Automated Trading Bot

An automated trading strategy for BTC/USD that detects chart patterns (Head & Shoulders, Double Top, Rectangles) and executes trades with proper risk management.

## Features

- **Pattern Detection**: Erect H&S, Inverted H&S, Double Top, Rectangle patterns
- **Trend Analysis**: Multiple trend detection methods (HH/HL, Moving Averages, Linear Regression)
- **News Filtering**: Integrates with economic calendars to avoid high-impact news events
- **Risk Management**: Position sizing, daily loss limits, concurrent trade limits
- **Multi-Timeframe**: Supports 1h, 2h, and other timeframes
- **Dry Run Mode**: Test strategies without risking real money
- **Comprehensive Logging**: Track all trades and events

## Architecture

```
src/bitoki/
├── config.py           # Configuration management
├── strategy.py         # Main strategy orchestration
├── main.py            # Entry point
├── data/
│   ├── market_data.py # OHLCV data fetching via CCXT
│   └── news.py        # Economic news calendar integration
├── patterns/
│   ├── trend.py       # Trend detection
│   └── detector.py    # Chart pattern detection
├── risk/
│   ├── position_sizer.py  # Position sizing calculations
│   └── risk_manager.py    # Risk management and safety checks
├── trading/
│   └── executor.py    # Order execution
└── utils/
    └── logger.py      # Logging configuration
```

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone or navigate to the repository:
   ```bash
   cd c:\Users\adminidiakhoa\Demo\BITOKI
   ```

2. Install dependencies using uv:
   ```bash
   uv pip install -e .
   ```

3. Create your environment file:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your exchange API credentials:
   ```
   EXCHANGE_API_KEY=your_api_key_here
   EXCHANGE_API_SECRET=your_api_secret_here
   TRADE_MODE=dry_run  # Change to 'live' for real trading
   ```

5. Review and adjust configuration in `config/strategy_config.yaml`

## Configuration

Edit `config/strategy_config.yaml` to customize:

- **Symbol**: Trading pair (default: BTC/USD)
- **Timeframes**: Which timeframes to analyze
- **Patterns**: Which patterns to trade
- **Risk**: Risk percentage, take profit, stop loss parameters
- **Safety**: Daily loss limits, max trades per day
- **Trading Mode**: `dry_run` or `live`

## Usage

### Dry Run Mode (Recommended for Testing)

```bash
uv run python -m bitoki.main
```

This will simulate trades without placing real orders.

### Live Trading Mode

**⚠️ WARNING: Live mode trades with real money. Use at your own risk!**

1. Set `trade_mode: "live"` in `config/strategy_config.yaml` OR
2. Set `TRADE_MODE=live` in `.env` file

Then run:
```bash
uv run python -m bitoki.main
```

## Strategy Logic

1. **Data Fetch**: Fetch OHLCV data for configured timeframes (1h, 2h)
2. **News Check**: Check for high-impact USD economic news
3. **Trend Detection**: Analyze market trend (bullish/bearish/sideways)
4. **Pattern Detection**: Scan for configured chart patterns
5. **Pattern Confirmation**: Wait for retest and rejection
6. **Risk Checks**: Verify safety limits (daily loss, concurrent trades, etc.)
7. **Position Sizing**: Calculate position size based on 2% risk rule
8. **Order Execution**: Place market/limit order with SL and TP
9. **Monitoring**: Track open positions and PnL

## Pattern Entry Rules

| Pattern | Entry Side | Entry Condition | Stop Loss | Take Profit |
|---------|-----------|-----------------|-----------|-------------|
| Erect H&S | SELL | Retest of right shoulder + rejection | Above right shoulder | Entry - 200 pips |
| Inverted H&S | BUY | Retest of right shoulder + rejection | Below right shoulder | Entry + 200 pips |
| Double Top | SELL | Retest of neckline + rejection | Above highest peak | Entry - 200 pips |
| Erect Rectangle | BUY | Breakout above resistance + retest | Below support | Entry + 200 pips |
| Inverted Rectangle | SELL | Breakdown below support + retest | Above resistance | Entry - 200 pips |

## Risk Management

- **Position Sizing**: 2% of account balance per trade
- **Stop Loss**: Structure-based or ATR-based fallback
- **Take Profit**: Fixed 200 pips
- **Max Concurrent Trades**: 3
- **Daily Loss Limit**: 10% of account balance
- **Max Daily Trades**: 10
- **News Blocking**: No trades 30 minutes before/after high-impact news

## Monitoring and Logs

Logs are written to:
- Console (stdout)
- `logs/strategy.log` (rotated daily, kept for 30 days)

Monitor the bot's activity:
```bash
tail -f logs/strategy.log
```

## Testing

Run tests (when available):
```bash
uv run pytest tests/
```

## Supported Exchanges

The bot uses CCXT and supports any CCXT-compatible exchange. Default is Binance.

To change exchange, edit `config/strategy_config.yaml`:
```yaml
exchange:
  name: "binance"  # or "kraken", "bybit", etc.
```

## Troubleshooting

### "Config file not found"
Ensure `config/strategy_config.yaml` exists

### "API credentials not configured"
Add your API key and secret to `.env` file

### "Insufficient data for pattern detection"
Wait for more candles to accumulate, or reduce `min_pattern_bars` in code

### "No OHLCV data returned"
Check your internet connection and exchange API status

## Disclaimer

**IMPORTANT**: This trading bot is provided for educational purposes only.

- Cryptocurrency trading involves substantial risk of loss
- Past performance is not indicative of future results
- Never invest more than you can afford to lose
- The developers are not responsible for any financial losses
- Always test thoroughly in dry-run mode before live trading
- Monitor your bot regularly and set appropriate risk limits
- You are solely responsible for your trading decisions

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/bitoki/issues
- Documentation: See this README

## Development

Built with:
- Python 3.10+
- CCXT for exchange connectivity
- Pandas for data manipulation
- Loguru for logging
- uv for dependency management
# BITOKI
