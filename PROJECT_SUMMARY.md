# BITOKI Project Summary

## Overview

BITOKI is a fully automated BTC/USD trading bot that detects chart patterns and executes trades with comprehensive risk management. Built for live trading with safety features and proper position sizing.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Main Strategy Loop                      │
│                     (strategy.py)                            │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──► Market Data (data/market_data.py)
             │    └─► CCXT Exchange Integration
             │        └─► Fetches OHLCV candles
             │
             ├──► News Checker (data/news.py)
             │    └─► ForexFactory scraper
             │        └─► Blocks trades during high-impact news
             │
             ├──► Trend Detector (patterns/trend.py)
             │    └─► HH/HL, Moving Averages, Linear Regression
             │        └─► Returns: bullish, bearish, sideways
             │
             ├──► Pattern Detector (patterns/detector.py)
             │    └─► Detects: H&S, Inv H&S, Double Top, Rectangles
             │        └─► Validates retest & rejection
             │
             ├──► Position Sizer (risk/position_sizer.py)
             │    └─► Calculates size based on 2% risk rule
             │        └─► SL: structure-based or ATR fallback
             │
             ├──► Risk Manager (risk/risk_manager.py)
             │    └─► Enforces daily limits & concurrent trades
             │        └─► Tracks PnL and statistics
             │
             └──► Order Executor (trading/executor.py)
                  └─► Places orders via CCXT
                      └─► Market/Limit with SL and TP
```

## Core Components

### 1. Data Layer (`src/bitoki/data/`)

- **market_data.py**: OHLCV fetching via CCXT
  - Supports multiple exchanges
  - Rate limiting built-in
  - Balance and ticker queries

- **news.py**: Economic calendar integration
  - ForexFactory scraper
  - High-impact event detection
  - Configurable news blocking window

### 2. Pattern Detection (`src/bitoki/patterns/`)

- **trend.py**: Multi-method trend detection
  - Higher Highs/Higher Lows
  - EMA crossovers (20/50)
  - Linear regression slope
  - ADX-based trend strength

- **detector.py**: Chart pattern recognition
  - Erect Head & Shoulders
  - Inverted Head & Shoulders
  - Double Top
  - Erect Rectangle (bullish breakout)
  - Inverted Rectangle (bearish breakdown)
  - Retest confirmation logic

### 3. Risk Management (`src/bitoki/risk/`)

- **position_sizer.py**: Position sizing calculations
  - 2% risk per trade (configurable)
  - Structure-based stop loss
  - ATR-based fallback
  - Fixed take profit (200 pips)

- **risk_manager.py**: Safety enforcement
  - Max concurrent trades limit
  - Daily loss limit
  - Daily trade count limit
  - Trade tracking and statistics

### 4. Trading Execution (`src/bitoki/trading/`)

- **executor.py**: Order placement
  - Dry run mode (simulation)
  - Live mode (real trading)
  - Market and limit orders
  - Automatic SL/TP placement

### 5. Configuration & Utilities

- **config.py**: YAML configuration loader
- **utils/logger.py**: Loguru-based logging
- **strategy.py**: Main orchestration loop
- **main.py**: Entry point with safety checks

## Trading Logic Flow

```
1. START ITERATION
   │
2. FOR EACH TIMEFRAME (1h, 2h)
   │
3. ├─► Fetch OHLCV data (500 candles)
   │
4. ├─► Check for high-impact news
   │   └─► If YES → SKIP this timeframe
   │
5. ├─► Detect trend (bullish/bearish/sideways)
   │
6. ├─► Detect patterns
   │   └─► Filter by allowed patterns
   │
7. ├─► FOR EACH PATTERN
   │   │
8. │   ├─► Confirm retest + rejection
   │   │   └─► If NO → Skip
   │   │
9. │   ├─► Determine side (buy/sell)
   │   │
10.│   ├─► Calculate SL (structure or ATR)
   │   │
11.│   ├─► Calculate TP (entry ± 200 pips)
   │   │
12.│   ├─► Calculate position size (2% risk)
   │   │
13.│   ├─► Check risk limits
   │   │   └─► Concurrent trades, daily loss, etc.
   │   │   └─► If FAIL → Skip
   │   │
14.│   └─► Place order (market + SL + TP)
   │       └─► Track in risk manager
   │
15.└─► Print statistics
   │
16.SLEEP (poll_interval_seconds)
   │
17.REPEAT
```

## Pattern Entry Rules

| Pattern | Direction | Entry Trigger | Stop Loss Location | Take Profit |
|---------|-----------|---------------|-------------------|-------------|
| Erect H&S | SELL | Retest right shoulder + rejection down | Above right shoulder + padding | Entry - 200 pips |
| Inverted H&S | BUY | Retest right shoulder + rejection up | Below right shoulder - padding | Entry + 200 pips |
| Double Top | SELL | Retest neckline + rejection down | Above highest peak + padding | Entry - 200 pips |
| Erect Rectangle | BUY | Breakout above + retest + hold | Below support - padding | Entry + 200 pips |
| Inv Rectangle | SELL | Breakdown below + retest + hold | Above resistance + padding | Entry - 200 pips |

## Risk Management Rules

### Position Sizing
- Risk: 2% of account balance per trade
- Formula: `Size = (Balance × 0.02) / |Entry - StopLoss|`

### Stop Loss Methods
1. **Structure-based** (preferred):
   - H&S: At right shoulder level
   - Double Top: At highest peak
   - Rectangle: At support/resistance

2. **ATR-based** (fallback):
   - `SL = Entry ± (ATR × 2.0)`

### Take Profit
- Fixed: 200 pips from entry
- Direction: Based on trade side

### Safety Limits
- Max concurrent trades: 3
- Max daily trades: 10
- Daily loss limit: 10% of account
- News block window: 30 minutes

## Configuration

Located in `config/strategy_config.yaml`:

```yaml
# Trading parameters
symbol: "BTC/USD"
timeframes: ["1h", "2h"]
trade_mode: "live"  # or "dry_run"
order_type: "market"  # or "limit"

# Risk management
risk_pct: 0.02  # 2% per trade
take_profit_pips: 200
max_concurrent_trades: 3
daily_loss_limit_pct: 0.10
max_trades_per_day: 10

# Pattern detection
allowed_patterns:
  - ErectHnS
  - InvertedHnS
  - DoubleTop
  - ErectRect
  - InvRect

# Technical indicators
atr_period: 14
atr_multiplier: 2.0
stoploss_padding_points: 10

# News filtering
news_block_minutes: 30

# Execution
poll_interval_seconds: 60

# Exchange (configure via .env)
exchange:
  name: "binance"
  sandbox: true  # Set false for live
```

## Environment Variables

`.env` file:
```
EXCHANGE_API_KEY=your_api_key
EXCHANGE_API_SECRET=your_api_secret
TRADE_MODE=live  # Override config
```

## Installation & Usage

### Install
```bash
uv pip install -e .
```

### Configure
```bash
cp .env.example .env
# Edit .env with your credentials
# Edit config/strategy_config.yaml as needed
```

### Run
```bash
uv run python run.py
```

## File Structure

```
BITOKI/
├── src/bitoki/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Config loader
│   ├── strategy.py          # Main loop
│   ├── data/
│   │   ├── __init__.py
│   │   ├── market_data.py   # CCXT integration
│   │   └── news.py          # News checker
│   ├── patterns/
│   │   ├── __init__.py
│   │   ├── trend.py         # Trend detection
│   │   └── detector.py      # Pattern detection
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── position_sizer.py
│   │   └── risk_manager.py
│   ├── trading/
│   │   ├── __init__.py
│   │   └── executor.py      # Order execution
│   └── utils/
│       ├── __init__.py
│       └── logger.py
├── config/
│   └── strategy_config.yaml
├── logs/                    # Created at runtime
├── pyproject.toml          # Dependencies
├── .env                    # API credentials (create from .env.example)
├── run.py                  # Convenience runner
├── README.md
├── SETUP.md
├── QUICKSTART.md
└── PROJECT_SUMMARY.md (this file)
```

## Key Features

✅ **Automated Pattern Detection**
  - 5 pattern types with validation
  - Retest confirmation required
  - Symmetry and structure checks

✅ **Comprehensive Risk Management**
  - Position sizing (2% risk rule)
  - Multiple safety limits
  - Daily loss caps

✅ **News Integration**
  - Economic calendar monitoring
  - High-impact event filtering
  - Automatic trade blocking

✅ **Multi-Timeframe Analysis**
  - 1h and 2h timeframes
  - Extensible to others

✅ **Flexible Trading Modes**
  - Dry run (simulation)
  - Live (real trading)
  - Sandbox/testnet support

✅ **Robust Logging**
  - Console output
  - File logging (rotated daily)
  - Statistics tracking

## Testing Checklist

Before live trading:

- [ ] Run in dry_run mode for 24-48 hours
- [ ] Verify pattern detection works
- [ ] Check risk calculations are correct
- [ ] Confirm news blocking functions
- [ ] Test with small amounts on testnet
- [ ] Verify stop loss and take profit placement
- [ ] Monitor for any errors in logs

## Important Warnings

⚠️ **Trading Risks**
- Cryptocurrency trading is highly risky
- You can lose all your capital
- Past performance ≠ future results

⚠️ **Bot Limitations**
- Not guaranteed to be profitable
- Requires active monitoring
- Patterns are subjective and may fail
- Market conditions change

⚠️ **Security**
- Keep API keys secure
- Use read/trade permissions only (no withdrawals)
- IP whitelist your API keys
- Never share your .env file

## Support & Maintenance

- Check logs regularly in `logs/strategy.log`
- Monitor open positions on exchange
- Review statistics in console output
- Adjust configuration based on performance
- Keep dependencies updated via uv

## Future Enhancements (TODO)

- [ ] Backtesting module
- [ ] More pattern types (triangles, wedges)
- [ ] Telegram/Discord notifications
- [ ] Web dashboard for monitoring
- [ ] Machine learning pattern validation
- [ ] Multi-symbol support
- [ ] Advanced order types (trailing stops)
- [ ] Performance analytics dashboard

## License

MIT License - Use at your own risk

---

**Remember**: Always trade responsibly and never invest more than you can afford to lose. This bot is a tool, not a guarantee of profits.
