"""Wallet management API endpoints."""

from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class WalletBalance:
    """Represents a wallet balance."""
    currency: str
    balance: float
    usd_value: float
    address: str = ""


class WalletManager:
    """Manages cryptocurrency wallets and balances."""

    SUPPORTED_CURRENCIES = ["BTC", "ETH", "SOL", "USDT_ERC20", "USDT_TRC20", "NGN"]

    def __init__(self, exchange=None):
        """
        Initialize wallet manager.

        Args:
            exchange: CCXT exchange instance
        """
        self.exchange = exchange
        self._balances = {}

    def get_balances(self) -> List[WalletBalance]:
        """
        Get all wallet balances.

        Returns:
            List of WalletBalance objects
        """
        balances = []

        if self.exchange:
            try:
                exchange_balance = self.exchange.fetch_balance()

                for currency in self.SUPPORTED_CURRENCIES:
                    base_currency = currency.replace("_ERC20", "").replace("_TRC20", "")

                    if base_currency in exchange_balance.get("total", {}):
                        balance = exchange_balance["total"][base_currency]

                        # Get USD value (simplified - would need price feeds in production)
                        usd_value = self._get_usd_value(base_currency, balance)

                        balances.append(WalletBalance(
                            currency=currency,
                            balance=balance,
                            usd_value=usd_value,
                            address=""  # Would get from exchange
                        ))
                    else:
                        # Zero balance for currencies not in exchange
                        balances.append(WalletBalance(
                            currency=currency,
                            balance=0.0,
                            usd_value=0.0,
                            address=""
                        ))
            except Exception as e:
                print(f"Error fetching balances: {e}")
                # Return mock data on error
                return self._get_mock_balances()
        else:
            return self._get_mock_balances()

        return balances

    def _get_usd_value(self, currency: str, amount: float) -> float:
        """Get USD value of amount in given currency."""
        # Mock prices - in production, fetch real-time prices
        prices = {
            "BTC": 97000.0,
            "ETH": 3500.0,
            "SOL": 180.0,
            "USDT": 1.0,
            "NGN": 0.0012  # 1 USD = ~830 NGN
        }

        return amount * prices.get(currency, 0.0)

    def _get_mock_balances(self) -> List[WalletBalance]:
        """Get mock balances for testing."""
        return [
            WalletBalance("BTC", 0.0521, 5053.70, "bc1q..."),
            WalletBalance("ETH", 1.234, 4319.00, "0x..."),
            WalletBalance("SOL", 25.5, 4590.00, "Sol..."),
            WalletBalance("USDT_ERC20", 1500.0, 1500.00, "0x..."),
            WalletBalance("USDT_TRC20", 800.0, 800.00, "TR..."),
            WalletBalance("NGN", 500000.0, 602.41, ""),
        ]

    def get_total_balance_usd(self) -> float:
        """Get total portfolio value in USD."""
        return sum(b.usd_value for b in self.get_balances())

    def generate_deposit_address(self, currency: str) -> str:
        """
        Generate a deposit address for the given currency.

        Args:
            currency: Currency code

        Returns:
            Deposit address
        """
        # In production, use exchange API to generate real addresses
        if currency == "BTC":
            return "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
        elif currency == "ETH" or "ERC20" in currency:
            return "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        elif currency == "SOL":
            return "SoLXnHJKmGvGnRpqH3vWh6EvFy7XYi9kXvyMm8CXnF8"
        elif "TRC20" in currency:
            return "TRX9Jv8uPiNL8Z6swykP93FtMHPJLiQhBE"
        else:
            return f"Address_{currency}"

    def get_transaction_history(self, currency: str = None, limit: int = 50) -> List[Dict]:
        """
        Get transaction history.

        Args:
            currency: Filter by currency (optional)
            limit: Max number of transactions

        Returns:
            List of transaction dictionaries
        """
        # Mock transaction data
        transactions = [
            {
                "id": "tx_001",
                "type": "deposit",
                "currency": "BTC",
                "amount": 0.0521,
                "usd_value": 5053.70,
                "status": "completed",
                "timestamp": "2025-12-02T10:30:00",
                "address": "bc1q..."
            },
            {
                "id": "tx_002",
                "type": "withdrawal",
                "currency": "ETH",
                "amount": 0.5,
                "usd_value": 1750.00,
                "status": "completed",
                "timestamp": "2025-12-01T15:20:00",
                "address": "0x..."
            },
            {
                "id": "tx_003",
                "type": "trade",
                "currency": "USDT",
                "amount": 1500.0,
                "usd_value": 1500.00,
                "status": "completed",
                "timestamp": "2025-12-01T09:15:00",
                "address": "-"
            }
        ]

        if currency:
            transactions = [t for t in transactions if t["currency"] == currency]

        return transactions[:limit]
