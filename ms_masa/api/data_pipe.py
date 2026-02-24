"""
Data pipeline for aggregating Polymarket data across APIs.

Combines Gamma (discovery) and CLOB (order book) data into
unified market snapshots for agent consumption.
"""

from __future__ import annotations

import logging
from typing import Optional

from ms_masa.api.gamma import GammaClient
from ms_masa.api.clob import ClobClient
from ms_masa.config import MsMasaConfig
from ms_masa.models import Event, Market, MarketSnapshot, OrderBook

logger = logging.getLogger(__name__)


class DataPipeline:
    """Aggregates data from Gamma and CLOB APIs into unified views."""

    def __init__(self, config: Optional[MsMasaConfig] = None):
        self._config = config or MsMasaConfig()
        self.gamma = GammaClient(self._config)
        self.clob = ClobClient(self._config)

    def get_market_snapshot(self, market: Market) -> MarketSnapshot:
        """Build a complete snapshot of a market combining Gamma + CLOB data."""
        order_book: Optional[OrderBook] = None
        if market.yes_token:
            try:
                order_book = self.clob.get_order_book(market.yes_token)
            except Exception as e:
                logger.warning("Failed to fetch order book for %s: %s", market.id, e)

        return MarketSnapshot(
            market=market,
            order_book=order_book,
            volume_24h=market.volume,
            liquidity_score=self._compute_liquidity_score(order_book),
        )

    def get_tradeable_snapshots(self, limit: int = 50) -> list[MarketSnapshot]:
        """Get snapshots for all tradeable markets."""
        markets = self.gamma.get_tradeable_markets(limit=limit)
        snapshots = []
        for m in markets:
            try:
                snap = self.get_market_snapshot(m)
                snapshots.append(snap)
            except Exception as e:
                logger.warning("Skipping market %s: %s", m.id, e)
        return snapshots

    def get_event_with_books(self, event_id: str) -> Event:
        """Get event with order books hydrated on each market."""
        raw = self.gamma.get_event(event_id)
        event = GammaClient._parse_event(raw)
        return event

    def scan_markets_by_tag(self, tag: str, limit: int = 50) -> list[Market]:
        """Discover markets by tag (e.g., 'politics', 'crypto')."""
        raw = self.gamma.get_markets(limit=limit, tag=tag, active=True, closed=False)
        return [GammaClient._parse_market(m) for m in raw]

    def search_markets(self, query: str, limit: int = 50) -> list[Market]:
        """Search markets by question text (client-side filter)."""
        markets = self.gamma.get_tradeable_markets(limit=limit * 2)
        q_lower = query.lower()
        return [m for m in markets if q_lower in m.question.lower()][:limit]

    @staticmethod
    def _compute_liquidity_score(order_book: Optional[OrderBook]) -> float:
        """Score 0-1 indicating market liquidity health."""
        if not order_book or not order_book.bids or not order_book.asks:
            return 0.0
        depth = order_book.depth_bid + order_book.depth_ask
        spread_penalty = min(order_book.spread * 10, 1.0)
        raw = min(depth / 10000, 1.0) * (1.0 - spread_penalty)
        return round(max(raw, 0.0), 4)
