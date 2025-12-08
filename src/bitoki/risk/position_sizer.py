"""Position sizing calculations based on risk management rules."""

from typing import Optional
import pandas as pd
import numpy as np
from loguru import logger

from ..patterns.detector import Pattern


class PositionSizer:
    """Calculates position sizes based on risk parameters."""

    def __init__(
        self,
        risk_pct: float = 0.02,
        pips_unit_in_usd: float = 1.0,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
        stoploss_padding_points: float = 10
    ):
        """
        Initialize position sizer.

        Args:
            risk_pct: Percentage of account to risk per trade (e.g., 0.02 = 2%)
            pips_unit_in_usd: USD value of 1 pip
            atr_period: Period for ATR calculation
            atr_multiplier: Multiplier for ATR-based stop loss
            stoploss_padding_points: Additional padding for stop loss
        """
        self.risk_pct = risk_pct
        self.pips_unit_in_usd = pips_unit_in_usd
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.stoploss_padding_points = stoploss_padding_points

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """
        Calculate position size based on risk parameters.

        Formula: Position Size = (Account Balance × Risk %) / (Entry - Stop Loss)

        Args:
            account_balance: Total account balance in USD
            entry_price: Planned entry price
            stop_loss_price: Planned stop loss price

        Returns:
            Position size in BTC
        """
        if account_balance <= 0:
            logger.error("Account balance must be positive")
            return 0.0

        if entry_price <= 0 or stop_loss_price <= 0:
            logger.error("Entry and stop loss prices must be positive")
            return 0.0

        # Calculate risk amount in USD
        risk_amount = account_balance * self.risk_pct

        # Calculate stop loss distance in USD
        sl_distance = abs(entry_price - stop_loss_price)

        if sl_distance == 0:
            logger.error("Stop loss distance cannot be zero")
            return 0.0

        # Calculate position size
        position_size = risk_amount / sl_distance

        logger.debug(
            f"Position sizing: Balance=${account_balance:.2f}, "
            f"Risk=${risk_amount:.2f} ({self.risk_pct*100}%), "
            f"SL Distance=${sl_distance:.2f}, "
            f"Size={position_size:.6f} BTC"
        )

        return position_size

    def calculate_stop_loss(
        self,
        pattern: Pattern,
        ohlcv: pd.DataFrame,
        side: str
    ) -> float:
        """
        Calculate stop loss price based on pattern structure.

        Args:
            pattern: Detected pattern
            ohlcv: OHLCV data
            side: Trade side ('buy' or 'sell')

        Returns:
            Stop loss price
        """
        # Try structure-based stop loss first
        structural_sl = self._calculate_structural_stoploss(pattern, ohlcv, side)

        if structural_sl is not None:
            logger.debug(f"Using structural stop loss: {structural_sl:.2f}")
            return structural_sl

        # Fallback to ATR-based stop loss
        atr_sl = self._calculate_atr_stoploss(ohlcv, ohlcv['close'].iloc[-1], side)
        logger.debug(f"Using ATR-based stop loss: {atr_sl:.2f}")
        return atr_sl

    def _calculate_structural_stoploss(
        self,
        pattern: Pattern,
        ohlcv: pd.DataFrame,
        side: str
    ) -> Optional[float]:
        """
        Calculate stop loss based on pattern structure.

        Args:
            pattern: Detected pattern
            ohlcv: OHLCV data
            side: Trade side

        Returns:
            Stop loss price or None if cannot be determined
        """
        padding = self.stoploss_padding_points

        if pattern.type == "ErectHnS":
            # For short, SL above right shoulder
            if side == "sell" and pattern.right_shoulder:
                return pattern.right_shoulder + padding

        elif pattern.type == "InvertedHnS":
            # For long, SL below right shoulder
            if side == "buy" and pattern.right_shoulder:
                return pattern.right_shoulder - padding

        elif pattern.type == "DoubleTop":
            # For short, SL above highest peak
            if side == "sell":
                highest_peak = max(pattern.left_shoulder or 0, pattern.right_shoulder or 0)
                return highest_peak + padding

        elif pattern.type == "ErectRect":
            # For long after breakout, SL below rectangle bottom
            if side == "buy" and pattern.rectangle_bottom:
                return pattern.rectangle_bottom - padding

        elif pattern.type == "InvRect":
            # For short after breakdown, SL above rectangle top
            if side == "sell" and pattern.rectangle_top:
                return pattern.rectangle_top + padding

        return None

    def _calculate_atr_stoploss(
        self,
        ohlcv: pd.DataFrame,
        entry_price: float,
        side: str
    ) -> float:
        """
        Calculate ATR-based stop loss.

        Args:
            ohlcv: OHLCV data
            entry_price: Entry price
            side: Trade side

        Returns:
            Stop loss price
        """
        atr = self.calculate_atr(ohlcv)
        sl_distance = atr * self.atr_multiplier

        if side == "buy":
            return entry_price - sl_distance
        else:  # sell
            return entry_price + sl_distance

    def calculate_atr(self, ohlcv: pd.DataFrame) -> float:
        """
        Calculate Average True Range.

        Args:
            ohlcv: OHLCV DataFrame

        Returns:
            ATR value
        """
        df = ohlcv.copy()

        # Calculate True Range
        df['h-l'] = df['high'] - df['low']
        df['h-pc'] = abs(df['high'] - df['close'].shift(1))
        df['l-pc'] = abs(df['low'] - df['close'].shift(1))

        df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)

        # Calculate ATR
        atr = df['tr'].rolling(window=self.atr_period).mean().iloc[-1]

        return atr if not pd.isna(atr) else 0.0

    def calculate_take_profit(
        self,
        entry_price: float,
        side: str,
        pips: float
    ) -> float:
        """
        Calculate take profit price.

        Args:
            entry_price: Entry price
            side: Trade side ('buy' or 'sell')
            pips: Number of pips for take profit

        Returns:
            Take profit price
        """
        pip_value = pips * self.pips_unit_in_usd

        if side == "buy":
            return entry_price + pip_value
        else:  # sell
            return entry_price - pip_value

    def is_size_allowed(
        self,
        size: float,
        min_size: float = 0.0001,
        max_size: float = 100.0
    ) -> bool:
        """
        Check if position size is within allowed limits.

        Args:
            size: Position size to check
            min_size: Minimum allowed size
            max_size: Maximum allowed size

        Returns:
            True if size is valid
        """
        if size < min_size:
            logger.warning(f"Position size {size:.6f} below minimum {min_size}")
            return False

        if size > max_size:
            logger.warning(f"Position size {size:.6f} above maximum {max_size}")
            return False

        return True
