"""Main entry point for the BITOKI trading bot."""

import sys
import signal
from pathlib import Path

from .config import Config
from .utils.logger import setup_logger
from .strategy import TradingStrategy


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\n🛑 Shutdown signal received. Stopping strategy...")
    sys.exit(0)


def main():
    """Main function to run the trading strategy."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                  BITOKI Trading Bot v0.1.0                   ║
    ║           BTC/USD Pattern-Based Trading Strategy             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    # Load configuration
    config_path = Path("config/strategy_config.yaml")
    if not config_path.exists():
        print(f"❌ Error: Configuration file not found at {config_path}")
        print("Please create config/strategy_config.yaml from the example")
        sys.exit(1)

    try:
        config = Config(str(config_path))
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        sys.exit(1)

    # Setup logging
    logging_config = config.get('logging', {})
    setup_logger(logging_config)

    # Display configuration
    print(f"""
    Configuration:
    ─────────────────────────────────────────────────────────────
    Symbol:           {config.symbol}
    Timeframes:       {', '.join(config.timeframes)}
    Trade Mode:       {config.trade_mode.upper()}
    Order Type:       {config.order_type}
    Exchange:         {config.exchange_name}
    Sandbox Mode:     {config.is_sandbox}

    Risk Management:
    ─────────────────────────────────────────────────────────────
    Risk per Trade:   {config.risk_pct * 100}%
    Take Profit:      {config.take_profit_pips} pips
    Max Concurrent:   {config.max_concurrent_trades} trades
    Daily Loss Limit: {config.daily_loss_limit_pct * 100}%
    Max Daily Trades: {config.max_trades_per_day}

    Pattern Detection:
    ─────────────────────────────────────────────────────────────
    Allowed Patterns: {', '.join(config.allowed_patterns)}
    News Block Time:  {config.news_block_minutes} minutes
    Poll Interval:    {config.poll_interval_seconds} seconds
    """)

    # Warnings for live trading
    if config.trade_mode == "live":
        print("""
    ⚠️  WARNING: LIVE TRADING MODE ⚠️
    ═══════════════════════════════════════════════════════════
    You are about to run the bot in LIVE mode with REAL MONEY.

    IMPORTANT DISCLAIMERS:
    • Trading cryptocurrencies carries significant risk
    • Past performance does not guarantee future results
    • You may lose all of your invested capital
    • This bot is provided AS-IS with no warranties
    • The developers are not responsible for any losses
    • Always test thoroughly in dry-run mode first
    • Never invest more than you can afford to lose
    • Monitor your bot regularly and set appropriate limits
    ═══════════════════════════════════════════════════════════
        """)

        response = input("Type 'I UNDERSTAND THE RISKS' to continue: ")
        if response != "I UNDERSTAND THE RISKS":
            print("Exiting. Please run in dry_run mode for testing.")
            sys.exit(0)

        print("\n✅ Risk acknowledgment confirmed\n")

    # Check API credentials
    if not config.api_key or not config.api_secret:
        if config.trade_mode == "live":
            print("❌ Error: API credentials not configured")
            print("Please set EXCHANGE_API_KEY and EXCHANGE_API_SECRET in .env file")
            sys.exit(1)
        else:
            print("⚠️  Warning: API credentials not configured")
            print("   Running in dry-run mode with limited functionality\n")

    # Initialize and run strategy
    try:
        strategy = TradingStrategy(config)
        print("✅ Strategy initialized successfully\n")
        print("🚀 Starting main loop...\n")
        print("Press Ctrl+C to stop\n")

        strategy.run()

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
