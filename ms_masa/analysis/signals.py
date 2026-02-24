"""
Signal engine for detecting patterns and opportunities in Polymarket data.

Generates MarketSignal objects from market snapshots that agents can
use for decision-making. All signals are informational/analytical only.
"""

from __future__ import annotations

import logging
from typing import Optional

from ms_masa.models import MarketSignal, MarketSnapshot, OrderBook

logger = logging.getLogger(__name__)


class SignalEngine:
    """Generates analytical signals from market data."""

    def __init__(
        self,
        spread_threshold: float = 0.05,
        imbalance_threshold: float = 0.3,
        low_liquidity_threshold: float = 1000.0,
    ):
        self.spread_threshold = spread_threshold
        self.imbalance_threshold = imbalance_threshold
        self.low_liquidity_threshold = low_liquidity_threshold

    def generate_signals(self, snapshot: MarketSnapshot) -> list[MarketSignal]:
        """Generate all applicable signals for a market snapshot."""
        signals: list[MarketSignal] = []

        if snapshot.order_book:
            signals.extend(self._book_signals(snapshot))

        signals.extend(self._price_signals(snapshot))

        return signals

    def scan_snapshots(
        self, snapshots: list[MarketSnapshot]
    ) -> dict[str, list[MarketSignal]]:
        """Scan multiple snapshots, returning signals keyed by market ID."""
        result: dict[str, list[MarketSignal]] = {}
        for snap in snapshots:
            sigs = self.generate_signals(snap)
            if sigs:
                result[snap.market.id] = sigs
        return result

    # ── Book-based Signals ─────────────────────────────────────────────

    def _book_signals(self, snapshot: MarketSnapshot) -> list[MarketSignal]:
        signals: list[MarketSignal] = []
        book = snapshot.order_book
        if not book or not book.bids or not book.asks:
            return signals

        # Wide spread signal
        if book.spread > self.spread_threshold:
            signals.append(MarketSignal(
                market_id=snapshot.market.id,
                signal_type="wide_spread",
                strength=min(book.spread / 0.2, 1.0),
                description=f"Spread {book.spread:.4f} exceeds threshold {self.spread_threshold}",
                metadata={"spread": book.spread, "midpoint": book.midpoint},
            ))

        # Order book imbalance
        total = book.depth_bid + book.depth_ask
        if total > 0:
            imbalance = (book.depth_bid - book.depth_ask) / total
            if abs(imbalance) > self.imbalance_threshold:
                direction = "bid_heavy" if imbalance > 0 else "ask_heavy"
                signals.append(MarketSignal(
                    market_id=snapshot.market.id,
                    signal_type=f"imbalance_{direction}",
                    strength=imbalance,
                    description=f"Book imbalance {imbalance:.4f} ({direction})",
                    metadata={
                        "bid_depth": book.depth_bid,
                        "ask_depth": book.depth_ask,
                        "imbalance": imbalance,
                    },
                ))

        # Low liquidity warning
        if total < self.low_liquidity_threshold:
            signals.append(MarketSignal(
                market_id=snapshot.market.id,
                signal_type="low_liquidity",
                strength=1.0 - min(total / self.low_liquidity_threshold, 1.0),
                description=f"Total depth ${total:.0f} below threshold ${self.low_liquidity_threshold:.0f}",
                metadata={"total_depth": total},
            ))

        return signals

    # ── Price-based Signals ────────────────────────────────────────────

    def _price_signals(self, snapshot: MarketSnapshot) -> list[MarketSignal]:
        signals: list[MarketSignal] = []
        market = snapshot.market

        yes_p = market.yes_price
        if yes_p is None:
            return signals

        # Near-certainty signal
        if yes_p > 0.95 or yes_p < 0.05:
            signals.append(MarketSignal(
                market_id=market.id,
                signal_type="near_certainty",
                strength=abs(yes_p - 0.5) * 2,
                description=f"Market near certainty at {yes_p:.4f}",
                metadata={"yes_price": yes_p},
            ))

        # High-uncertainty signal (close to 50/50)
        if 0.45 < yes_p < 0.55:
            signals.append(MarketSignal(
                market_id=market.id,
                signal_type="high_uncertainty",
                strength=1.0 - abs(yes_p - 0.5) * 20,
                description=f"Market highly uncertain at {yes_p:.4f}",
                metadata={"yes_price": yes_p},
            ))

        return signals
