"""Gift card trading API."""

from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GiftCard:
    """Represents a gift card."""
    card_id: str
    brand: str
    country: str
    currency: str
    face_value: float
    buy_rate: float  # % of face value
    sell_rate: float  # % of face value
    category: str


@dataclass
class GiftCardTrade:
    """Represents a gift card trade."""
    trade_id: str
    card_id: str
    brand: str
    type: str  # buy or sell
    face_value: float
    rate: float
    amount_paid: float
    status: str
    timestamp: str


class GiftCardAPI:
    """Handles gift card trading operations."""

    # Supported gift card brands
    SUPPORTED_CARDS = [
        GiftCard("gc_001", "Amazon", "USA", "USD", 100, 0.82, 0.75, "Shopping"),
        GiftCard("gc_002", "iTunes", "USA", "USD", 50, 0.80, 0.73, "Entertainment"),
        GiftCard("gc_003", "Google Play", "USA", "USD", 100, 0.78, 0.71, "Entertainment"),
        GiftCard("gc_004", "Steam", "USA", "USD", 50, 0.81, 0.74, "Gaming"),
        GiftCard("gc_005", "Visa", "USA", "USD", 200, 0.85, 0.78, "General"),
        GiftCard("gc_006", "eBay", "USA", "USD", 100, 0.79, 0.72, "Shopping"),
        GiftCard("gc_007", "Walmart", "USA", "USD", 100, 0.83, 0.76, "Shopping"),
        GiftCard("gc_008", "Target", "USA", "USD", 50, 0.82, 0.75, "Shopping"),
        GiftCard("gc_009", "Nike", "USA", "USD", 100, 0.77, 0.70, "Fashion"),
        GiftCard("gc_010", "Sephora", "USA", "USD", 50, 0.78, 0.71, "Beauty"),
        GiftCard("gc_011", "Nordstrom", "USA", "USD", 100, 0.80, 0.73, "Fashion"),
        GiftCard("gc_012", "Xbox", "USA", "USD", 50, 0.81, 0.74, "Gaming"),
    ]

    def __init__(self):
        """Initialize gift card API."""
        self.cards = {card.card_id: card for card in self.SUPPORTED_CARDS}

    def get_available_cards(self, category: str = None) -> List[GiftCard]:
        """
        Get list of available gift cards.

        Args:
            category: Filter by category (optional)

        Returns:
            List of GiftCard objects
        """
        cards = list(self.cards.values())

        if category:
            cards = [c for c in cards if c.category == category]

        return cards

    def get_card_by_id(self, card_id: str) -> GiftCard:
        """Get gift card details by ID."""
        return self.cards.get(card_id)

    def get_card_by_brand(self, brand: str) -> List[GiftCard]:
        """Get gift cards by brand name."""
        return [c for c in self.cards.values() if brand.lower() in c.brand.lower()]

    def get_categories(self) -> List[str]:
        """Get list of gift card categories."""
        return list(set(c.category for c in self.cards.values()))

    def sell_gift_card(
        self,
        card_id: str,
        code: str,
        pin: str = None,
        face_value: float = None
    ) -> GiftCardTrade:
        """
        Sell a gift card.

        Args:
            card_id: Gift card ID
            code: Card code/number
            pin: Card PIN (if applicable)
            face_value: Face value (if different from default)

        Returns:
            GiftCardTrade object
        """
        card = self.get_card_by_id(card_id)

        if not card:
            raise ValueError(f"Card ID {card_id} not found")

        # Use provided face value or default
        value = face_value or card.face_value

        # Calculate payment amount
        amount_paid = value * card.sell_rate

        # Create trade
        import time
        trade_id = f"trade_{int(time.time() * 1000)}"

        trade = GiftCardTrade(
            trade_id=trade_id,
            card_id=card_id,
            brand=card.brand,
            type="sell",
            face_value=value,
            rate=card.sell_rate,
            amount_paid=amount_paid,
            status="pending",  # Would be verified in production
            timestamp=datetime.now().isoformat()
        )

        return trade

    def buy_gift_card(
        self,
        card_id: str,
        face_value: float,
        payment_method: str = "crypto"
    ) -> GiftCardTrade:
        """
        Buy a gift card.

        Args:
            card_id: Gift card ID
            face_value: Desired face value
            payment_method: Payment method (crypto, usdt, etc.)

        Returns:
            GiftCardTrade object
        """
        card = self.get_card_by_id(card_id)

        if not card:
            raise ValueError(f"Card ID {card_id} not found")

        # Calculate purchase amount
        amount_paid = face_value * card.buy_rate

        # Create trade
        import time
        trade_id = f"trade_{int(time.time() * 1000)}"

        trade = GiftCardTrade(
            trade_id=trade_id,
            card_id=card_id,
            brand=card.brand,
            type="buy",
            face_value=face_value,
            rate=card.buy_rate,
            amount_paid=amount_paid,
            status="completed",
            timestamp=datetime.now().isoformat()
        )

        return trade

    def get_trade_history(self, limit: int = 50) -> List[GiftCardTrade]:
        """
        Get gift card trade history.

        Args:
            limit: Max number of trades to return

        Returns:
            List of GiftCardTrade objects
        """
        # Mock trade history
        history = [
            GiftCardTrade(
                "trade_001",
                "gc_001",
                "Amazon",
                "sell",
                100.0,
                0.82,
                82.0,
                "completed",
                "2025-12-02T09:30:00"
            ),
            GiftCardTrade(
                "trade_002",
                "gc_002",
                "iTunes",
                "sell",
                50.0,
                0.80,
                40.0,
                "completed",
                "2025-12-01T14:20:00"
            ),
            GiftCardTrade(
                "trade_003",
                "gc_004",
                "Steam",
                "buy",
                50.0,
                0.81,
                40.5,
                "completed",
                "2025-11-30T11:15:00"
            )
        ]

        return history[:limit]

    def calculate_payout(self, card_id: str, face_value: float) -> Dict:
        """
        Calculate payout for selling a gift card.

        Args:
            card_id: Gift card ID
            face_value: Face value of card

        Returns:
            Dictionary with payout details
        """
        card = self.get_card_by_id(card_id)

        if not card:
            return {"error": "Card not found"}

        payout = face_value * card.sell_rate
        fee = face_value * 0.02  # 2% processing fee
        net_payout = payout - fee

        return {
            "face_value": face_value,
            "rate": card.sell_rate,
            "gross_payout": payout,
            "fee": fee,
            "net_payout": net_payout,
            "currency": card.currency
        }
