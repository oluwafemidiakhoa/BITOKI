"""Risk management and trade safety checks."""

from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class Trade:
    """Represents an executed trade."""

    order_id: str
    symbol: str
    side: str
    size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "open"  # open, closed, cancelled
    pnl: float = 0.0
    exit_price: float = 0.0
    pattern_type: str = ""


class RiskManager:
    """Manages trading risk and safety checks."""

    def __init__(
        self,
        max_concurrent_trades: int = 3,
        daily_loss_limit_pct: float = 0.10,
        max_trades_per_day: int = 10
    ):
        """
        Initialize risk manager.

        Args:
            max_concurrent_trades: Maximum number of simultaneous open trades
            daily_loss_limit_pct: Maximum daily loss as percentage of account
            max_trades_per_day: Maximum number of trades per day
        """
        self.max_concurrent_trades = max_concurrent_trades
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_trades_per_day = max_trades_per_day

        self.open_trades: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.daily_stats: Dict[str, dict] = {}

    def can_open_trade(
        self,
        account_balance: float,
        has_high_impact_news: bool = False
    ) -> tuple[bool, str]:
        """
        Check if a new trade can be opened based on risk rules.

        Args:
            account_balance: Current account balance
            has_high_impact_news: Whether high-impact news is nearby

        Returns:
            Tuple of (can_trade, reason)
        """
        # Check concurrent trades limit
        if len(self.open_trades) >= self.max_concurrent_trades:
            return False, f"Max concurrent trades reached ({self.max_concurrent_trades})"

        # Check daily trade limit
        today = datetime.now().date().isoformat()
        daily_trades = self.daily_stats.get(today, {}).get('trade_count', 0)
        if daily_trades >= self.max_trades_per_day:
            return False, f"Max daily trades reached ({self.max_trades_per_day})"

        # Check daily loss limit
        daily_pnl = self.daily_stats.get(today, {}).get('pnl', 0.0)
        max_loss = account_balance * self.daily_loss_limit_pct

        if daily_pnl < -max_loss:
            return False, f"Daily loss limit reached (${abs(daily_pnl):.2f} / ${max_loss:.2f})"

        # Check news
        if has_high_impact_news:
            return False, "High-impact news nearby"

        return True, "OK"

    def add_trade(self, trade: Trade) -> None:
        """
        Add a new trade to tracking.

        Args:
            trade: Trade object to add
        """
        self.open_trades.append(trade)

        # Update daily stats
        today = datetime.now().date().isoformat()
        if today not in self.daily_stats:
            self.daily_stats[today] = {'trade_count': 0, 'pnl': 0.0}

        self.daily_stats[today]['trade_count'] += 1

        logger.info(
            f"Trade added: {trade.side} {trade.size} {trade.symbol} @ {trade.entry_price} "
            f"(SL: {trade.stop_loss}, TP: {trade.take_profit})"
        )

    def close_trade(
        self,
        order_id: str,
        exit_price: float,
        status: str = "closed"
    ) -> None:
        """
        Close an open trade and update statistics.

        Args:
            order_id: ID of the trade to close
            exit_price: Exit price
            status: Status of closure (closed, stopped, target)
        """
        # Find trade
        trade = None
        for t in self.open_trades:
            if t.order_id == order_id:
                trade = t
                break

        if not trade:
            logger.warning(f"Trade {order_id} not found in open trades")
            return

        # Calculate PnL
        if trade.side == "buy":
            pnl = (exit_price - trade.entry_price) * trade.size
        else:  # sell
            pnl = (trade.entry_price - exit_price) * trade.size

        trade.exit_price = exit_price
        trade.pnl = pnl
        trade.status = status

        # Move to closed trades
        self.open_trades.remove(trade)
        self.closed_trades.append(trade)

        # Update daily stats
        today = datetime.now().date().isoformat()
        if today not in self.daily_stats:
            self.daily_stats[today] = {'trade_count': 0, 'pnl': 0.0}

        self.daily_stats[today]['pnl'] += pnl

        logger.info(
            f"Trade closed: {trade.order_id} - PnL: ${pnl:.2f} "
            f"({'+' if pnl > 0 else ''}{(pnl/trade.entry_price/trade.size)*100:.2f}%)"
        )

    def get_open_trade_count(self) -> int:
        """Get number of currently open trades."""
        return len(self.open_trades)

    def get_daily_pnl(self) -> float:
        """Get today's profit/loss."""
        today = datetime.now().date().isoformat()
        return self.daily_stats.get(today, {}).get('pnl', 0.0)

    def get_daily_trade_count(self) -> int:
        """Get today's trade count."""
        today = datetime.now().date().isoformat()
        return self.daily_stats.get(today, {}).get('trade_count', 0)

    def get_statistics(self) -> dict:
        """
        Get trading statistics.

        Returns:
            Dictionary with various statistics
        """
        if not self.closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
            }

        wins = [t for t in self.closed_trades if t.pnl > 0]
        losses = [t for t in self.closed_trades if t.pnl <= 0]

        total_pnl = sum(t.pnl for t in self.closed_trades)
        avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0.0
        avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0.0

        return {
            'total_trades': len(self.closed_trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': len(wins) / len(self.closed_trades) * 100 if self.closed_trades else 0.0,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': max((t.pnl for t in wins), default=0.0),
            'largest_loss': min((t.pnl for t in losses), default=0.0),
            'open_trades': len(self.open_trades),
            'daily_pnl': self.get_daily_pnl(),
            'daily_trades': self.get_daily_trade_count(),
        }

    def cleanup_old_stats(self, days_to_keep: int = 30) -> None:
        """
        Clean up old daily statistics.

        Args:
            days_to_keep: Number of days to keep
        """
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date().isoformat()
        keys_to_remove = [k for k in self.daily_stats.keys() if k < cutoff_date]

        for key in keys_to_remove:
            del self.daily_stats[key]

        if keys_to_remove:
            logger.info(f"Cleaned up {len(keys_to_remove)} days of old statistics")
