"""Order execution and management using CCXT."""

from typing import Optional, Dict, Any
import ccxt
from loguru import logger


class OrderResult:
    """Result of an order execution."""

    def __init__(self, success: bool, order_id: str = "", error: str = "", data: dict = None):
        self.success = success
        self.order_id = order_id
        self.error = error
        self.data = data or {}

    def __repr__(self) -> str:
        if self.success:
            return f"<OrderResult: Success, ID={self.order_id}>"
        else:
            return f"<OrderResult: Failed, Error={self.error}>"


class OrderExecutor:
    """Executes and manages trading orders."""

    def __init__(
        self,
        exchange: ccxt.Exchange,
        trade_mode: str = "dry_run",
        order_type: str = "market"
    ):
        """
        Initialize order executor.

        Args:
            exchange: CCXT exchange instance
            trade_mode: 'dry_run' or 'live'
            order_type: 'market' or 'limit'
        """
        self.exchange = exchange
        self.trade_mode = trade_mode.lower()
        self.order_type = order_type.lower()

        if self.trade_mode == "live":
            logger.warning("🚨 LIVE TRADING MODE ENABLED - Real money at risk!")
        else:
            logger.info("Running in DRY RUN mode - No real orders will be placed")

    def place_order(
        self,
        symbol: str,
        side: str,
        size: float,
        entry_price: float,
        sl_price: float,
        tp_price: float,
        meta: Optional[Dict[str, Any]] = None
    ) -> OrderResult:
        """
        Place a trading order with stop loss and take profit.

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            side: 'buy' or 'sell'
            size: Position size
            entry_price: Entry price (used for limit orders)
            sl_price: Stop loss price
            tp_price: Take profit price
            meta: Additional metadata for logging

        Returns:
            OrderResult object
        """
        meta = meta or {}

        logger.info(
            f"{'[DRY RUN] ' if self.trade_mode == 'dry_run' else ''}Placing {side} order: "
            f"{size:.6f} {symbol} @ {entry_price:.2f} "
            f"(SL: {sl_price:.2f}, TP: {tp_price:.2f}) "
            f"Pattern: {meta.get('pattern', 'N/A')}"
        )

        # Dry run mode - simulate order
        if self.trade_mode == "dry_run":
            return self._simulate_order(symbol, side, size, entry_price, sl_price, tp_price, meta)

        # Live mode - place real order
        try:
            # Place main order
            if self.order_type == "market":
                order = self._place_market_order(symbol, side, size)
            else:  # limit
                order = self._place_limit_order(symbol, side, size, entry_price)

            if not order:
                return OrderResult(success=False, error="Failed to place main order")

            order_id = order['id']
            actual_entry = order.get('price', entry_price)

            # Place stop loss order
            sl_order = self._place_stop_loss(symbol, side, size, sl_price, order_id)
            if not sl_order:
                logger.warning(f"Failed to place stop loss for order {order_id}")

            # Place take profit order
            tp_order = self._place_take_profit(symbol, side, size, tp_price, order_id)
            if not tp_order:
                logger.warning(f"Failed to place take profit for order {order_id}")

            logger.info(f"✅ Order placed successfully: {order_id}")

            return OrderResult(
                success=True,
                order_id=order_id,
                data={
                    'order': order,
                    'sl_order': sl_order,
                    'tp_order': tp_order,
                    'actual_entry': actual_entry,
                    'meta': meta
                }
            )

        except ccxt.InsufficientFunds as e:
            error_msg = f"Insufficient funds: {e}"
            logger.error(error_msg)
            return OrderResult(success=False, error=error_msg)

        except ccxt.InvalidOrder as e:
            error_msg = f"Invalid order: {e}"
            logger.error(error_msg)
            return OrderResult(success=False, error=error_msg)

        except ccxt.NetworkError as e:
            error_msg = f"Network error: {e}"
            logger.error(error_msg)
            return OrderResult(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            return OrderResult(success=False, error=error_msg)

    def _simulate_order(
        self,
        symbol: str,
        side: str,
        size: float,
        entry_price: float,
        sl_price: float,
        tp_price: float,
        meta: dict
    ) -> OrderResult:
        """Simulate order placement for dry run mode."""
        import time
        order_id = f"DRY_{int(time.time() * 1000)}"

        logger.info(f"[DRY RUN] Simulated order placed: {order_id}")

        return OrderResult(
            success=True,
            order_id=order_id,
            data={
                'symbol': symbol,
                'side': side,
                'size': size,
                'entry_price': entry_price,
                'sl_price': sl_price,
                'tp_price': tp_price,
                'meta': meta,
                'simulated': True
            }
        )

    def _place_market_order(self, symbol: str, side: str, size: float) -> Optional[dict]:
        """Place a market order."""
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=size
            )
            return order
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return None

    def _place_limit_order(
        self,
        symbol: str,
        side: str,
        size: float,
        price: float
    ) -> Optional[dict]:
        """Place a limit order."""
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=size,
                price=price
            )
            return order
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return None

    def _place_stop_loss(
        self,
        symbol: str,
        side: str,
        size: float,
        stop_price: float,
        reduce_only_order_id: str = None
    ) -> Optional[dict]:
        """
        Place a stop loss order.

        Args:
            symbol: Trading pair
            side: Opposite of main order ('sell' for long, 'buy' for short)
            size: Position size
            stop_price: Stop loss trigger price
            reduce_only_order_id: Main order ID (for reduce-only)
        """
        try:
            # Reverse side for stop loss
            sl_side = 'sell' if side == 'buy' else 'buy'

            # Different exchanges have different stop loss implementations
            # This is a generic approach - adjust for your specific exchange
            params = {
                'stopPrice': stop_price,
                'reduceOnly': True,
            }

            order = self.exchange.create_order(
                symbol=symbol,
                type='stop_market',  # or 'stop_limit' depending on exchange
                side=sl_side,
                amount=size,
                params=params
            )

            logger.debug(f"Stop loss order placed: {order.get('id')}")
            return order

        except Exception as e:
            logger.error(f"Error placing stop loss: {e}")
            return None

    def _place_take_profit(
        self,
        symbol: str,
        side: str,
        size: float,
        tp_price: float,
        reduce_only_order_id: str = None
    ) -> Optional[dict]:
        """
        Place a take profit order.

        Args:
            symbol: Trading pair
            side: Opposite of main order
            size: Position size
            tp_price: Take profit price
            reduce_only_order_id: Main order ID
        """
        try:
            # Reverse side for take profit
            tp_side = 'sell' if side == 'buy' else 'buy'

            params = {
                'reduceOnly': True,
            }

            order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=tp_side,
                amount=size,
                price=tp_price,
                params=params
            )

            logger.debug(f"Take profit order placed: {order.get('id')}")
            return order

        except Exception as e:
            logger.error(f"Error placing take profit: {e}")
            return None

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Order ID to cancel
            symbol: Trading pair

        Returns:
            True if successful
        """
        if self.trade_mode == "dry_run":
            logger.info(f"[DRY RUN] Would cancel order: {order_id}")
            return True

        try:
            self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def get_order_status(self, order_id: str, symbol: str) -> Optional[dict]:
        """
        Get status of an order.

        Args:
            order_id: Order ID
            symbol: Trading pair

        Returns:
            Order details or None
        """
        if self.trade_mode == "dry_run":
            logger.debug(f"[DRY RUN] Order status check: {order_id}")
            return {'id': order_id, 'status': 'open', 'simulated': True}

        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            return None
