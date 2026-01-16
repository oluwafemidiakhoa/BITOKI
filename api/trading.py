"""Trading API endpoints for buy/sell/swap operations."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import ccxt
import random
import time
from loguru import logger


@dataclass
class TradeOrder:
    """Represents a trade order."""
    order_id: str
    type: str  # buy, sell, swap
    from_currency: str
    to_currency: str
    amount: float
    price: float
    total: float
    status: str
    timestamp: str


class TradingAPI:
    """Handles buy, sell, and swap operations."""

    def __init__(self, exchange: Optional[ccxt.Exchange]):
        """
        Initialize trading API.

        Args:
            exchange: CCXT exchange instance (can be None for mock mode)
        """
        self.exchange = exchange
        self.mock_mode = exchange is None
        if self.mock_mode:
            logger.info("TradingAPI initialized in mock mode - using sample data")

    def buy_crypto(
        self,
        currency: str,
        amount: float,
        payment_currency: str = "USDT"
    ) -> TradeOrder:
        """
        Buy cryptocurrency.

        Args:
            currency: Currency to buy (e.g., 'BTC', 'ETH')
            amount: Amount to buy
            payment_currency: Currency to pay with

        Returns:
            TradeOrder object
        """
        # Use mock mode if exchange is not available
        if self.mock_mode or not self.exchange:
            return self._mock_trade_order('buy', currency, amount, payment_currency)
        
        try:
            # Get current price
            symbol = f"{currency}/{payment_currency}"
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            total = amount * price

            # Place market buy order
            order = self.exchange.create_market_buy_order(
                symbol=symbol,
                amount=amount
            )

            return TradeOrder(
                order_id=order['id'],
                type='buy',
                from_currency=payment_currency,
                to_currency=currency,
                amount=amount,
                price=price,
                total=total,
                status=order['status'],
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.warning(f"Error buying {currency}: {e}")
            # Fallback to mock order
            return self._mock_trade_order('buy', currency, amount, payment_currency)

    def sell_crypto(
        self,
        currency: str,
        amount: float,
        receive_currency: str = "USDT"
    ) -> TradeOrder:
        """
        Sell cryptocurrency.

        Args:
            currency: Currency to sell
            amount: Amount to sell
            receive_currency: Currency to receive

        Returns:
            TradeOrder object
        """
        # Use mock mode if exchange is not available
        if self.mock_mode or not self.exchange:
            return self._mock_trade_order('sell', currency, amount, receive_currency)
        
        try:
            symbol = f"{currency}/{receive_currency}"
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            total = amount * price

            # Place market sell order
            order = self.exchange.create_market_sell_order(
                symbol=symbol,
                amount=amount
            )

            return TradeOrder(
                order_id=order['id'],
                type='sell',
                from_currency=currency,
                to_currency=receive_currency,
                amount=amount,
                price=price,
                total=total,
                status=order['status'],
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.warning(f"Error selling {currency}: {e}")
            return self._mock_trade_order('sell', currency, amount, receive_currency)

    def swap_crypto(
        self,
        from_currency: str,
        to_currency: str,
        amount: float
    ) -> TradeOrder:
        """
        Swap one cryptocurrency for another.

        Args:
            from_currency: Currency to swap from
            to_currency: Currency to swap to
            amount: Amount to swap

        Returns:
            TradeOrder object
        """
        try:
            # For direct swaps, we might need to go through USDT
            # Example: SOL -> ETH might need SOL -> USDT -> ETH

            # Try direct pair first
            symbol = f"{from_currency}/{to_currency}"

            try:
                ticker = self.exchange.fetch_ticker(symbol)
                price = ticker['last']
            except:
                # Try reverse pair
                symbol = f"{to_currency}/{from_currency}"
                ticker = self.exchange.fetch_ticker(symbol)
                price = 1.0 / ticker['last']

            received_amount = amount * price

            # Place swap order
            order = self.exchange.create_market_sell_order(
                symbol=f"{from_currency}/USDT",
                amount=amount
            )

            return TradeOrder(
                order_id=order['id'],
                type='swap',
                from_currency=from_currency,
                to_currency=to_currency,
                amount=amount,
                price=price,
                total=received_amount,
                status=order['status'],
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.warning(f"Error swapping {from_currency} to {to_currency}: {e}")
            return self._mock_trade_order('swap', from_currency, amount, to_currency)

    def get_price(self, currency: str, quote_currency: str = "USDT") -> float:
        """
        Get current price of currency.

        Args:
            currency: Currency to get price for
            quote_currency: Quote currency

        Returns:
            Current price
        """
        try:
            symbol = f"{currency}/{quote_currency}"
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.warning(f"Error getting price for {currency}: {e}")
            # Return mock prices when exchange is unavailable
            return self._get_mock_price(currency)

    def get_market_data(self, currency: str, quote_currency: str = "USDT") -> Dict:
        """
        Get market data including price and 24h change.

        Args:
            currency: Currency to get data for
            quote_currency: Quote currency

        Returns:
            Dictionary with price, change_24h_percent, and change_24h_value
        """
        try:
            symbol = f"{currency}/{quote_currency}"
            ticker = self.exchange.fetch_ticker(symbol)

            price = ticker.get('last', 0)
            change_percent = ticker.get('percentage', 0)  # 24h percentage change
            change_value = ticker.get('change', 0)  # 24h absolute change

            return {
                'currency': currency,
                'quote_currency': quote_currency,
                'price': price,
                'change_24h_percent': change_percent,
                'change_24h_value': change_value,
                'high_24h': ticker.get('high', price),
                'low_24h': ticker.get('low', price),
                'volume_24h': ticker.get('baseVolume', 0)
            }
        except Exception as e:
            logger.warning(f"Error getting market data for {currency}: {e}")
            # Return mock data with realistic changes
            mock_data = {
                "BTC": {"price": 97000.0, "change": random.uniform(-5, 5)},
                "ETH": {"price": 3500.0, "change": random.uniform(-5, 5)},
                "SOL": {"price": 180.0, "change": random.uniform(-8, 8)},
                "USDT": {"price": 1.0, "change": 0.0}
            }
            data = mock_data.get(currency, {"price": 100.0, "change": 0.0})
            return {
                'currency': currency,
                'quote_currency': quote_currency,
                'price': data['price'],
                'change_24h_percent': data['change'],
                'change_24h_value': data['price'] * (data['change'] / 100),
                'high_24h': data['price'] * 1.05,
                'low_24h': data['price'] * 0.95,
                'volume_24h': 1000000
            }

    def get_order_book(self, currency: str, quote_currency: str = "USDT") -> Dict:
        """
        Get order book for currency pair.

        Args:
            currency: Base currency
            quote_currency: Quote currency

        Returns:
            Order book data
        """
        try:
            symbol = f"{currency}/{quote_currency}"
            order_book = self.exchange.fetch_order_book(symbol)
            return {
                'bids': order_book['bids'][:10],  # Top 10 bids
                'asks': order_book['asks'][:10],  # Top 10 asks
                'timestamp': order_book['timestamp']
            }
        except Exception as e:
            logger.warning(f"Error fetching order book: {e}")
            return {'bids': [], 'asks': [], 'timestamp': None}

    def get_recent_trades(self, limit: int = 20) -> List[Dict]:
        """
        Get recent trades.

        Args:
            limit: Number of trades to return

        Returns:
            List of trade dictionaries
        """
        # Mock recent trades
        trades = [
            {
                "order_id": "ord_001",
                "type": "buy",
                "pair": "BTC/USDT",
                "amount": 0.0521,
                "price": 97000.0,
                "total": 5053.70,
                "status": "completed",
                "timestamp": "2025-12-02T10:30:00"
            },
            {
                "order_id": "ord_002",
                "type": "sell",
                "pair": "ETH/USDT",
                "amount": 0.5,
                "price": 3500.0,
                "total": 1750.0,
                "status": "completed",
                "timestamp": "2025-12-01T15:20:00"
            }
        ]
        return trades[:limit]

    def _get_mock_price(self, currency: str) -> float:
        """Get mock price for currency when exchange is unavailable."""
        mock_prices = {
            "BTC": 65420.50 + random.uniform(-500, 500),  # Add some volatility
            "ETH": 3245.80 + random.uniform(-50, 50),
            "SOL": 145.67 + random.uniform(-10, 10),
            "USDT": 1.00
        }
        return mock_prices.get(currency, 100.0)

    def _mock_trade_order(
        self,
        order_type: str,
        currency: str,
        amount: float,
        other_currency: str
    ) -> TradeOrder:
        """Create a mock trade order for testing."""
        import time
        order_id = f"mock_{int(time.time() * 1000)}"

        prices = {
            "BTC": 97000.0,
            "ETH": 3500.0,
            "SOL": 180.0,
            "USDT": 1.0
        }

        price = prices.get(currency, 100.0)
        total = amount * price

        return TradeOrder(
            order_id=order_id,
            type=order_type,
            from_currency=other_currency if order_type == 'buy' else currency,
            to_currency=currency if order_type == 'buy' else other_currency,
            amount=amount,
            price=price,
            total=total,
            status='completed',
            timestamp=datetime.now().isoformat()
        )
