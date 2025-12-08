"""Main trading strategy orchestration."""

import time
from datetime import datetime
from typing import Dict, List
import pandas as pd
from loguru import logger

from .config import Config
from .data.market_data import MarketDataFetcher
from .data.news import NewsChecker
from .patterns.trend import TrendDetector
from .patterns.detector import PatternDetector, Pattern
from .risk.position_sizer import PositionSizer
from .risk.risk_manager import RiskManager, Trade
from .trading.executor import OrderExecutor


class TradingStrategy:
    """Main BTC/USD automated trading strategy."""

    def __init__(self, config: Config):
        """
        Initialize trading strategy.

        Args:
            config: Configuration object
        """
        self.config = config

        # Initialize components
        self.market_data = MarketDataFetcher(
            exchange_name=config.exchange_name,
            api_key=config.api_key,
            api_secret=config.api_secret,
            sandbox=config.is_sandbox
        )

        self.news_checker = NewsChecker(target_currency="USD")
        self.trend_detector = TrendDetector(lookback_period=50)
        self.pattern_detector = PatternDetector(
            min_pattern_bars=20,
            max_pattern_bars=100,
            symmetry_tolerance=0.15
        )

        self.position_sizer = PositionSizer(
            risk_pct=config.risk_pct,
            pips_unit_in_usd=config.pips_unit_in_usd,
            atr_period=config.atr_period,
            atr_multiplier=config.atr_multiplier,
            stoploss_padding_points=config.stoploss_padding_points
        )

        self.risk_manager = RiskManager(
            max_concurrent_trades=config.max_concurrent_trades,
            daily_loss_limit_pct=config.daily_loss_limit_pct,
            max_trades_per_day=config.max_trades_per_day
        )

        self.order_executor = OrderExecutor(
            exchange=self.market_data.exchange,
            trade_mode=config.trade_mode,
            order_type=config.order_type
        )

        self.running = False
        logger.info("Trading strategy initialized")

    def run(self) -> None:
        """
        Main strategy loop.

        Continuously monitors market, detects patterns, and executes trades.
        """
        self.running = True
        logger.info("🚀 Starting trading strategy...")

        iteration = 0

        try:
            while self.running:
                iteration += 1
                logger.info(f"=== Iteration {iteration} ===")

                # Process each timeframe
                for timeframe in self.config.timeframes:
                    self._process_timeframe(timeframe)

                # Print statistics
                self._print_statistics()

                # Wait for next iteration
                logger.info(f"Sleeping for {self.config.poll_interval_seconds} seconds...")
                time.sleep(self.config.poll_interval_seconds)

        except KeyboardInterrupt:
            logger.info("Strategy stopped by user")
        except Exception as e:
            logger.error(f"Strategy error: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Strategy shutdown complete")

    def _process_timeframe(self, timeframe: str) -> None:
        """
        Process a single timeframe for trading signals.

        Args:
            timeframe: Timeframe to process (e.g., '1h', '2h')
        """
        logger.info(f"Processing {timeframe} timeframe...")

        try:
            # 1. Fetch OHLCV data
            ohlcv = self.market_data.fetch_ohlcv(
                symbol=self.config.symbol,
                timeframe=timeframe,
                limit=500
            )

            if ohlcv.empty:
                logger.warning(f"No OHLCV data for {timeframe}, skipping...")
                return

            # 2. Check for high-impact news
            has_high_impact_news = self.news_checker.has_high_impact_within(
                minutes=self.config.news_block_minutes
            )

            if has_high_impact_news:
                logger.warning(
                    f"High-impact news within {self.config.news_block_minutes} minutes. "
                    f"Skipping {timeframe}"
                )
                return

            # 3. Detect trend
            trend = self.trend_detector.detect_trend(ohlcv)
            trend_strength = self.trend_detector.get_trend_strength(ohlcv)
            logger.info(f"Trend: {trend} (strength: {trend_strength:.2f})")

            # 4. Detect patterns
            patterns = self.pattern_detector.detect_patterns(ohlcv)

            if not patterns:
                logger.debug(f"No patterns detected on {timeframe}")
                return

            logger.info(f"Detected {len(patterns)} pattern(s): {[p.type for p in patterns]}")

            # 5. Process each pattern
            for pattern in patterns:
                self._process_pattern(pattern, ohlcv, timeframe, trend)

        except Exception as e:
            logger.error(f"Error processing {timeframe}: {e}", exc_info=True)

    def _process_pattern(
        self,
        pattern: Pattern,
        ohlcv: pd.DataFrame,
        timeframe: str,
        trend: str
    ) -> None:
        """
        Process a detected pattern for potential trade entry.

        Args:
            pattern: Detected pattern
            ohlcv: OHLCV data
            timeframe: Current timeframe
            trend: Detected trend
        """
        # Filter by allowed patterns
        if pattern.type not in self.config.allowed_patterns:
            logger.debug(f"Pattern {pattern.type} not in allowed list, skipping")
            return

        # Confirm retest
        if not self.pattern_detector.confirm_retest(pattern, ohlcv):
            logger.debug(f"Pattern {pattern.type} retest not confirmed, skipping")
            return

        logger.info(f"✅ Pattern {pattern.type} confirmed with retest!")

        # Determine trade side
        side = self._get_trade_side(pattern)
        if not side:
            logger.warning(f"Could not determine trade side for {pattern.type}")
            return

        # Get current price and account balance
        current_price = ohlcv['close'].iloc[-1]
        entry_price = current_price  # For market orders

        try:
            balance_info = self.market_data.get_balance()
            # Get available balance (adjust key based on your exchange)
            account_balance = balance_info.get('total', {}).get('USDT', 0.0)

            if account_balance <= 0:
                logger.warning("Account balance is zero or unavailable")
                return

        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return

        # Calculate stop loss
        sl_price = self.position_sizer.calculate_stop_loss(pattern, ohlcv, side)

        # Calculate take profit
        tp_price = self.position_sizer.calculate_take_profit(
            entry_price=entry_price,
            side=side,
            pips=self.config.take_profit_pips
        )

        # Calculate position size
        position_size = self.position_sizer.calculate_position_size(
            account_balance=account_balance,
            entry_price=entry_price,
            stop_loss_price=sl_price
        )

        # Validate position size
        if not self.position_sizer.is_size_allowed(position_size):
            logger.warning(f"Position size {position_size} not allowed, skipping")
            return

        # Check risk management rules
        can_trade, reason = self.risk_manager.can_open_trade(
            account_balance=account_balance,
            has_high_impact_news=False  # Already checked above
        )

        if not can_trade:
            logger.warning(f"Cannot open trade: {reason}")
            return

        # Place order
        logger.info(
            f"Placing {side} order for {pattern.type} pattern:\n"
            f"  Entry: ${entry_price:.2f}\n"
            f"  SL: ${sl_price:.2f}\n"
            f"  TP: ${tp_price:.2f}\n"
            f"  Size: {position_size:.6f} BTC\n"
            f"  Risk: ${account_balance * self.config.risk_pct:.2f} "
            f"({self.config.risk_pct * 100}%)"
        )

        order_result = self.order_executor.place_order(
            symbol=self.config.symbol,
            side=side,
            size=position_size,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            meta={
                'pattern': pattern.type,
                'timeframe': timeframe,
                'trend': trend,
                'detected_at': datetime.now().isoformat()
            }
        )

        if order_result.success:
            # Add to risk manager
            trade = Trade(
                order_id=order_result.order_id,
                symbol=self.config.symbol,
                side=side,
                size=position_size,
                entry_price=entry_price,
                stop_loss=sl_price,
                take_profit=tp_price,
                pattern_type=pattern.type
            )
            self.risk_manager.add_trade(trade)

            logger.info(f"✅ Trade executed successfully: {order_result.order_id}")
        else:
            logger.error(f"❌ Trade execution failed: {order_result.error}")

    def _get_trade_side(self, pattern: Pattern) -> str:
        """
        Determine trade side based on pattern type.

        Args:
            pattern: Pattern object

        Returns:
            'buy' or 'sell' or empty string
        """
        if pattern.type == "ErectHnS":
            return "sell"
        elif pattern.type == "InvertedHnS":
            return "buy"
        elif pattern.type == "DoubleTop":
            return "sell"
        elif pattern.type == "ErectRect":
            return "buy"
        elif pattern.type == "InvRect":
            return "sell"
        else:
            return ""

    def _print_statistics(self) -> None:
        """Print current trading statistics."""
        stats = self.risk_manager.get_statistics()

        logger.info(
            f"\n📊 Statistics:\n"
            f"  Open trades: {stats['open_trades']}\n"
            f"  Today's trades: {stats['daily_trades']}\n"
            f"  Today's PnL: ${stats['daily_pnl']:.2f}\n"
            f"  Total trades: {stats['total_trades']}\n"
            f"  Win rate: {stats['win_rate']:.1f}%\n"
            f"  Total PnL: ${stats['total_pnl']:.2f}"
        )

    def stop(self) -> None:
        """Stop the strategy gracefully."""
        logger.info("Stopping strategy...")
        self.running = False
