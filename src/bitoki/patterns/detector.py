"""Pattern detection for Head & Shoulders, Double Top, and Rectangle patterns."""

from dataclasses import dataclass
from typing import List, Optional, Literal
from datetime import datetime
import pandas as pd
import numpy as np
from loguru import logger


PatternType = Literal["ErectHnS", "InvertedHnS", "DoubleTop", "ErectRect", "InvRect"]


@dataclass
class Pattern:
    """Represents a detected chart pattern."""

    type: PatternType
    formation_bar_index: int
    neckline_price: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    # Pattern-specific fields
    left_shoulder: Optional[float] = None
    head: Optional[float] = None
    right_shoulder: Optional[float] = None
    rectangle_top: Optional[float] = None
    rectangle_bottom: Optional[float] = None

    valid_since: Optional[datetime] = None
    confidence: float = 0.0

    def __repr__(self) -> str:
        return f"<Pattern: {self.type} @ {self.neckline_price:.2f} (conf={self.confidence:.2f})>"


class PatternDetector:
    """Detects chart patterns in OHLCV data."""

    def __init__(
        self,
        min_pattern_bars: int = 20,
        max_pattern_bars: int = 100,
        symmetry_tolerance: float = 0.15
    ):
        """
        Initialize pattern detector.

        Args:
            min_pattern_bars: Minimum bars for pattern formation
            max_pattern_bars: Maximum bars for pattern formation
            symmetry_tolerance: Tolerance for symmetry checks (0-1)
        """
        self.min_pattern_bars = min_pattern_bars
        self.max_pattern_bars = max_pattern_bars
        self.symmetry_tolerance = symmetry_tolerance

    def detect_patterns(self, ohlcv: pd.DataFrame) -> List[Pattern]:
        """
        Detect all configured patterns in OHLCV data.

        Args:
            ohlcv: DataFrame with OHLCV data

        Returns:
            List of detected Pattern objects
        """
        if len(ohlcv) < self.min_pattern_bars:
            logger.warning(f"Insufficient data for pattern detection: {len(ohlcv)} candles")
            return []

        patterns = []

        # Detect each pattern type
        patterns.extend(self._detect_head_and_shoulders(ohlcv, erect=True))
        patterns.extend(self._detect_head_and_shoulders(ohlcv, erect=False))
        patterns.extend(self._detect_double_top(ohlcv))
        patterns.extend(self._detect_rectangles(ohlcv, erect=True))
        patterns.extend(self._detect_rectangles(ohlcv, erect=False))

        logger.info(f"Detected {len(patterns)} patterns")
        return patterns

    def _detect_head_and_shoulders(self, ohlcv: pd.DataFrame, erect: bool = True) -> List[Pattern]:
        """
        Detect Head and Shoulders (or Inverted H&S) patterns.

        Pattern structure:
        - Erect H&S: Left shoulder (peak) -> Head (higher peak) -> Right shoulder (peak)
        - Inverted: Left shoulder (trough) -> Head (lower trough) -> Right shoulder (trough)

        Args:
            ohlcv: OHLCV DataFrame
            erect: True for erect H&S, False for inverted

        Returns:
            List of detected patterns
        """
        patterns = []
        df = ohlcv.copy()

        # Find swing points
        window = 5
        if erect:
            df['swing'] = df['high'].rolling(window=window*2+1, center=True).max() == df['high']
            price_col = 'high'
        else:
            df['swing'] = df['low'].rolling(window=window*2+1, center=True).min() == df['low']
            price_col = 'low'

        swing_points = df[df['swing']].copy()

        if len(swing_points) < 3:
            return patterns

        # Iterate through potential H&S patterns
        for i in range(len(swing_points) - 2):
            left_idx = swing_points.index[i]
            head_idx = swing_points.index[i + 1]
            right_idx = swing_points.index[i + 2]

            left_price = swing_points.iloc[i][price_col]
            head_price = swing_points.iloc[i + 1][price_col]
            right_price = swing_points.iloc[i + 2][price_col]

            # Check pattern structure
            if erect:
                # Head should be higher than shoulders
                if not (head_price > left_price and head_price > right_price):
                    continue
            else:
                # Head should be lower than shoulders
                if not (head_price < left_price and head_price < right_price):
                    continue

            # Check shoulder symmetry
            shoulder_diff = abs(left_price - right_price)
            shoulder_avg = (left_price + right_price) / 2
            symmetry_ratio = shoulder_diff / shoulder_avg if shoulder_avg != 0 else 1

            if symmetry_ratio > self.symmetry_tolerance:
                continue

            # Calculate neckline (connect lows between shoulders for erect, highs for inverted)
            if erect:
                # Find lows between left shoulder and head, head and right shoulder
                left_trough = df.loc[left_idx:head_idx, 'low'].min()
                right_trough = df.loc[head_idx:right_idx, 'low'].min()
                neckline = (left_trough + right_trough) / 2
            else:
                # Find highs between left shoulder and head, head and right shoulder
                left_peak = df.loc[left_idx:head_idx, 'high'].max()
                right_peak = df.loc[head_idx:right_idx, 'high'].max()
                neckline = (left_peak + right_peak) / 2

            # Calculate confidence based on symmetry and pattern clarity
            confidence = 1.0 - symmetry_ratio

            # Check if pattern is recent enough
            bars_since = len(df) - df.index.get_loc(right_idx)
            if bars_since > 20:  # Pattern too old
                continue

            pattern = Pattern(
                type="ErectHnS" if erect else "InvertedHnS",
                formation_bar_index=df.index.get_loc(right_idx),
                neckline_price=neckline,
                left_shoulder=left_price,
                head=head_price,
                right_shoulder=right_price,
                valid_since=datetime.now(),
                confidence=confidence
            )

            patterns.append(pattern)
            logger.debug(f"Detected {pattern}")

        return patterns

    def _detect_double_top(self, ohlcv: pd.DataFrame) -> List[Pattern]:
        """
        Detect Double Top patterns.

        Pattern: Two peaks at similar levels with a trough in between.

        Args:
            ohlcv: OHLCV DataFrame

        Returns:
            List of detected patterns
        """
        patterns = []
        df = ohlcv.copy()

        # Find swing highs
        window = 5
        df['swing_high'] = df['high'].rolling(window=window*2+1, center=True).max() == df['high']
        swing_highs = df[df['swing_high']].copy()

        if len(swing_highs) < 2:
            return patterns

        # Iterate through potential double tops
        for i in range(len(swing_highs) - 1):
            first_idx = swing_highs.index[i]
            second_idx = swing_highs.index[i + 1]

            first_peak = swing_highs.iloc[i]['high']
            second_peak = swing_highs.iloc[i + 1]['high']

            # Check if peaks are at similar levels
            peak_diff = abs(first_peak - second_peak)
            peak_avg = (first_peak + second_peak) / 2
            similarity_ratio = peak_diff / peak_avg if peak_avg != 0 else 1

            if similarity_ratio > self.symmetry_tolerance:
                continue

            # Find trough between peaks
            trough = df.loc[first_idx:second_idx, 'low'].min()
            neckline = trough

            # Check depth (trough should be significantly lower than peaks)
            depth = peak_avg - trough
            depth_ratio = depth / peak_avg
            if depth_ratio < 0.02:  # At least 2% retracement
                continue

            # Calculate confidence
            confidence = 1.0 - similarity_ratio

            # Check recency
            bars_since = len(df) - df.index.get_loc(second_idx)
            if bars_since > 20:
                continue

            pattern = Pattern(
                type="DoubleTop",
                formation_bar_index=df.index.get_loc(second_idx),
                neckline_price=neckline,
                left_shoulder=first_peak,  # Reuse fields
                right_shoulder=second_peak,
                valid_since=datetime.now(),
                confidence=confidence
            )

            patterns.append(pattern)
            logger.debug(f"Detected {pattern}")

        return patterns

    def _detect_rectangles(self, ohlcv: pd.DataFrame, erect: bool = True) -> List[Pattern]:
        """
        Detect Rectangle (consolidation) patterns.

        Pattern: Price consolidates between support and resistance levels.

        Args:
            ohlcv: OHLCV DataFrame
            erect: True for bullish breakout, False for bearish

        Returns:
            List of detected patterns
        """
        patterns = []
        df = ohlcv.tail(100).copy()  # Look at recent data

        if len(df) < self.min_pattern_bars:
            return patterns

        # Calculate support and resistance levels
        window = 10
        df['resistance'] = df['high'].rolling(window=window).max()
        df['support'] = df['low'].rolling(window=window).min()

        # Look for consolidation zones
        for i in range(len(df) - self.min_pattern_bars, len(df)):
            lookback = df.iloc[i-self.min_pattern_bars:i]

            resistance = lookback['high'].max()
            support = lookback['low'].min()

            # Check if range is tight (consolidation)
            range_size = resistance - support
            mid_price = (resistance + support) / 2
            range_ratio = range_size / mid_price

            # Consolidation should be within 5-15% range
            if range_ratio < 0.02 or range_ratio > 0.15:
                continue

            # Check if price touched both levels multiple times
            touches_resistance = (lookback['high'] >= resistance * 0.99).sum()
            touches_support = (lookback['low'] <= support * 1.01).sum()

            if touches_resistance < 2 or touches_support < 2:
                continue

            # Check for breakout
            current_price = df.iloc[i]['close']
            if erect and current_price > resistance:
                neckline = resistance
            elif not erect and current_price < support:
                neckline = support
            else:
                continue

            pattern = Pattern(
                type="ErectRect" if erect else "InvRect",
                formation_bar_index=i,
                neckline_price=neckline,
                rectangle_top=resistance,
                rectangle_bottom=support,
                valid_since=datetime.now(),
                confidence=0.7
            )

            patterns.append(pattern)
            logger.debug(f"Detected {pattern}")

        return patterns

    def confirm_retest(self, pattern: Pattern, ohlcv: pd.DataFrame) -> bool:
        """
        Confirm that pattern has retested key level and shown rejection.

        Args:
            pattern: Pattern to check
            ohlcv: Current OHLCV data

        Returns:
            True if retest confirmed with rejection
        """
        if len(ohlcv) < 5:
            return False

        recent = ohlcv.tail(10)
        current_price = recent['close'].iloc[-1]

        if pattern.type == "ErectHnS":
            # Look for retest of right shoulder and rejection downward
            target_level = pattern.right_shoulder
            tolerance = target_level * 0.02  # 2% tolerance

            # Check if price recently tested the level
            tested = any(
                abs(recent['high'].iloc[i] - target_level) <= tolerance
                for i in range(-5, 0)
            )

            # Check for rejection (price should be below target now)
            rejected = current_price < target_level * 0.98

            return tested and rejected

        elif pattern.type == "InvertedHnS":
            # Look for retest of right shoulder and rejection upward
            target_level = pattern.right_shoulder
            tolerance = target_level * 0.02

            tested = any(
                abs(recent['low'].iloc[i] - target_level) <= tolerance
                for i in range(-5, 0)
            )

            rejected = current_price > target_level * 1.02

            return tested and rejected

        elif pattern.type == "DoubleTop":
            # Look for retest of neckline (support) and rejection downward
            target_level = pattern.neckline_price
            tolerance = target_level * 0.02

            tested = any(
                abs(recent['low'].iloc[i] - target_level) <= tolerance
                for i in range(-5, 0)
            )

            rejected = current_price < target_level * 0.98

            return tested and rejected

        elif pattern.type in ["ErectRect", "InvRect"]:
            # Look for retest after breakout
            target_level = pattern.neckline_price
            tolerance = target_level * 0.02

            if pattern.type == "ErectRect":
                # Bullish breakout - retest from above
                tested = any(
                    abs(recent['low'].iloc[i] - target_level) <= tolerance
                    for i in range(-5, 0)
                )
                rejected = current_price > target_level * 1.01
            else:
                # Bearish breakout - retest from below
                tested = any(
                    abs(recent['high'].iloc[i] - target_level) <= tolerance
                    for i in range(-5, 0)
                )
                rejected = current_price < target_level * 0.99

            return tested and rejected

        return False
