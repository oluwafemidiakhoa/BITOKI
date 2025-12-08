"""Market data fetching using CCXT."""

from typing import Optional, List
import pandas as pd
import ccxt
from loguru import logger


class MarketDataFetcher:
    """Fetches OHLCV data from cryptocurrency exchanges."""

    def __init__(self, exchange_name: str, api_key: str = "", api_secret: str = "", sandbox: bool = True):
        """
        Initialize market data fetcher.

        Args:
            exchange_name: Name of the exchange (e.g., 'binance', 'kraken')
            api_key: API key for the exchange
            api_secret: API secret for the exchange
            sandbox: Use sandbox/testnet mode
        """
        self.exchange_name = exchange_name
        self.exchange = self._initialize_exchange(exchange_name, api_key, api_secret, sandbox)
        logger.info(f"Initialized {exchange_name} exchange (sandbox={sandbox})")

    def _initialize_exchange(
        self,
        exchange_name: str,
        api_key: str,
        api_secret: str,
        sandbox: bool
    ) -> ccxt.Exchange:
        """Initialize CCXT exchange instance."""
        try:
            exchange_class = getattr(ccxt, exchange_name)
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # Use futures for BTC/USD
                }
            })

            if sandbox and hasattr(exchange, 'set_sandbox_mode'):
                exchange.set_sandbox_mode(True)

            return exchange

        except AttributeError:
            raise ValueError(f"Exchange '{exchange_name}' not supported by CCXT")
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from exchange.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USD')
            timeframe: Candle timeframe (e.g., '1h', '2h', '4h', '1d')
            limit: Number of candles to fetch
            since: Timestamp in ms to fetch data from

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            logger.debug(f"Fetching {limit} {timeframe} candles for {symbol}")

            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                since=since
            )

            if not ohlcv:
                logger.warning(f"No OHLCV data returned for {symbol} {timeframe}")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            logger.info(f"Fetched {len(df)} candles for {symbol} {timeframe}")
            return df

        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching OHLCV: {e}")
            raise
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error fetching OHLCV: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching OHLCV: {e}")
            raise

    def get_ticker(self, symbol: str) -> dict:
        """
        Get current ticker data for symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            Dictionary with ticker data (last, bid, ask, etc.)
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            logger.debug(f"Ticker for {symbol}: {ticker.get('last')}")
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            raise

    def get_balance(self) -> dict:
        """
        Get account balance.

        Returns:
            Dictionary with balance information
        """
        try:
            balance = self.exchange.fetch_balance()
            logger.debug(f"Account balance fetched")
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise
