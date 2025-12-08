"""Trend detection using Higher Highs/Higher Lows and moving averages."""

from typing import Literal
import pandas as pd
import numpy as np
from loguru import logger


TrendType = Literal["bullish", "bearish", "sideways"]


class TrendDetector:
    """Detects market trends using multiple methods."""

    def __init__(self, lookback_period: int = 50):
        """
        Initialize trend detector.

        Args:
            lookback_period: Number of candles to analyze for trend
        """
        self.lookback_period = lookback_period

    def detect_trend(self, ohlcv: pd.DataFrame) -> TrendType:
        """
        Detect overall trend using multiple indicators.

        Args:
            ohlcv: DataFrame with OHLCV data

        Returns:
            "bullish", "bearish", or "sideways"
        """
        if len(ohlcv) < self.lookback_period:
            logger.warning(f"Insufficient data for trend detection: {len(ohlcv)} candles")
            return "sideways"

        # Use multiple methods and combine results
        hh_hl_trend = self._detect_hh_hl_trend(ohlcv)
        ma_trend = self._detect_ma_trend(ohlcv)
        slope_trend = self._detect_slope_trend(ohlcv)

        # Weighted voting system
        trends = [hh_hl_trend, ma_trend, slope_trend]
        bullish_count = trends.count("bullish")
        bearish_count = trends.count("bearish")

        if bullish_count >= 2:
            return "bullish"
        elif bearish_count >= 2:
            return "bearish"
        else:
            return "sideways"

    def _detect_hh_hl_trend(self, ohlcv: pd.DataFrame) -> TrendType:
        """
        Detect trend using Higher Highs/Higher Lows pattern.

        Bullish: Series of higher highs and higher lows
        Bearish: Series of lower highs and lower lows
        """
        df = ohlcv.tail(self.lookback_period).copy()

        # Find swing highs and lows
        window = 5
        df['swing_high'] = df['high'].rolling(window=window*2+1, center=True).max() == df['high']
        df['swing_low'] = df['low'].rolling(window=window*2+1, center=True).min() == df['low']

        # Get last few swing points
        swing_highs = df[df['swing_high']]['high'].tail(3)
        swing_lows = df[df['swing_low']]['low'].tail(3)

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            # Check for higher highs and higher lows
            higher_highs = all(swing_highs.iloc[i] < swing_highs.iloc[i+1]
                             for i in range(len(swing_highs)-1))
            higher_lows = all(swing_lows.iloc[i] < swing_lows.iloc[i+1]
                            for i in range(len(swing_lows)-1))

            # Check for lower highs and lower lows
            lower_highs = all(swing_highs.iloc[i] > swing_highs.iloc[i+1]
                            for i in range(len(swing_highs)-1))
            lower_lows = all(swing_lows.iloc[i] > swing_lows.iloc[i+1]
                           for i in range(len(swing_lows)-1))

            if higher_highs and higher_lows:
                return "bullish"
            elif lower_highs and lower_lows:
                return "bearish"

        return "sideways"

    def _detect_ma_trend(self, ohlcv: pd.DataFrame) -> TrendType:
        """
        Detect trend using moving average crossovers.

        Uses 20 and 50 period EMAs.
        """
        df = ohlcv.tail(self.lookback_period).copy()

        # Calculate EMAs
        df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()

        # Get recent values
        latest = df.iloc[-1]
        prev = df.iloc[-5] if len(df) >= 5 else df.iloc[-1]

        # Check alignment
        price_above_ma = latest['close'] > latest['ema_20'] > latest['ema_50']
        price_below_ma = latest['close'] < latest['ema_20'] < latest['ema_50']

        # Check if crossover occurred recently
        bullish_cross = (prev['ema_20'] <= prev['ema_50'] and
                        latest['ema_20'] > latest['ema_50'])
        bearish_cross = (prev['ema_20'] >= prev['ema_50'] and
                        latest['ema_20'] < latest['ema_50'])

        if price_above_ma or bullish_cross:
            return "bullish"
        elif price_below_ma or bearish_cross:
            return "bearish"
        else:
            return "sideways"

    def _detect_slope_trend(self, ohlcv: pd.DataFrame) -> TrendType:
        """
        Detect trend using linear regression slope.

        Positive slope = bullish
        Negative slope = bearish
        """
        df = ohlcv.tail(self.lookback_period).copy()

        # Calculate linear regression
        x = np.arange(len(df))
        y = df['close'].values

        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]

        # Normalize slope by price (percentage slope)
        avg_price = df['close'].mean()
        normalized_slope = (slope / avg_price) * 100

        # Threshold for sideways (e.g., ±0.1% per candle)
        threshold = 0.05

        if normalized_slope > threshold:
            return "bullish"
        elif normalized_slope < -threshold:
            return "bearish"
        else:
            return "sideways"

    def get_trend_strength(self, ohlcv: pd.DataFrame) -> float:
        """
        Get trend strength as a value between 0 and 1.

        Args:
            ohlcv: DataFrame with OHLCV data

        Returns:
            Trend strength (0 = no trend, 1 = very strong trend)
        """
        if len(ohlcv) < 20:
            return 0.0

        df = ohlcv.tail(50).copy()

        # Calculate ADX (Average Directional Index) as trend strength
        # Simplified calculation
        df['tr'] = pd.concat([
            df['high'] - df['low'],
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        ], axis=1).max(axis=1)

        df['plus_dm'] = np.where(
            (df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
            np.maximum(df['high'] - df['high'].shift(1), 0),
            0
        )

        df['minus_dm'] = np.where(
            (df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
            np.maximum(df['low'].shift(1) - df['low'], 0),
            0
        )

        period = 14
        df['atr'] = df['tr'].rolling(window=period).mean()
        df['plus_di'] = 100 * (df['plus_dm'].rolling(window=period).mean() / df['atr'])
        df['minus_di'] = 100 * (df['minus_dm'].rolling(window=period).mean() / df['atr'])

        df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
        df['adx'] = df['dx'].rolling(window=period).mean()

        # Return normalized ADX (0-1 scale, where 25+ is strong trend)
        adx_value = df['adx'].iloc[-1]
        return min(adx_value / 50, 1.0) if not pd.isna(adx_value) else 0.0
