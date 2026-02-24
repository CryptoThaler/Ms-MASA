"""
Market analyzer for Polymarket prediction markets.

Provides structural analysis of markets, order books, and events
to identify opportunities, patterns, and market characteristics.
"""

from __future__ import annotations

import logging
from typing import Optional

from ms_masa.models import (
    Event,
    Market,
    MarketSignal,
    MarketSnapshot,
    OrderBook,
)

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """Analyzes Polymarket markets for structural patterns and opportunities."""

    # ── Order Book Analysis ────────────────────────────────────────────

    @staticmethod
    def analyze_order_book(book: OrderBook) -> dict:
        """Produce a compact analysis of an order book."""
        if not book.bids and not book.asks:
            return {"status": "empty", "tradeable": False}

        best_bid = max(b.price for b in book.bids) if book.bids else 0.0
        best_ask = min(a.price for a in book.asks) if book.asks else 1.0
        bid_depth = sum(b.size for b in book.bids)
        ask_depth = sum(a.size for a in book.asks)
        total_depth = bid_depth + ask_depth

        # Depth concentration at best levels
        bid_top3 = sum(
            b.size for b in sorted(book.bids, key=lambda x: -x.price)[:3]
        )
        ask_top3 = sum(
            a.size for a in sorted(book.asks, key=lambda x: x.price)[:3]
        )

        return {
            "status": "active",
            "tradeable": True,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": round(best_ask - best_bid, 6),
            "midpoint": round((best_bid + best_ask) / 2, 6),
            "bid_depth": round(bid_depth, 2),
            "ask_depth": round(ask_depth, 2),
            "total_depth": round(total_depth, 2),
            "bid_top3_concentration": round(bid_top3 / bid_depth, 4) if bid_depth else 0,
            "ask_top3_concentration": round(ask_top3 / ask_depth, 4) if ask_depth else 0,
            "imbalance": round((bid_depth - ask_depth) / total_depth, 4) if total_depth else 0,
            "bid_levels": len(book.bids),
            "ask_levels": len(book.asks),
        }

    # ── Market Characterization ────────────────────────────────────────

    @staticmethod
    def characterize_market(market: Market) -> dict:
        """Produce a compact characterization of a market."""
        yes_p = market.yes_price or 0.5
        return {
            "id": market.id,
            "question": market.question,
            "status": market.status,
            "tradeable": market.is_tradeable,
            "yes_price": yes_p,
            "no_price": market.no_price,
            "implied_prob": round(yes_p, 4),
            "volume": market.volume,
            "liquidity": market.liquidity,
            "neg_risk": market.neg_risk,
            "category": market.category,
            "outcomes": market.outcomes,
            "tags": market.tags,
            "certainty": round(abs(yes_p - 0.5) * 2, 4),  # 0=uncertain, 1=certain
        }

    # ── Snapshot Analysis ──────────────────────────────────────────────

    @staticmethod
    def analyze_snapshot(snapshot: MarketSnapshot) -> dict:
        """Full analysis of a market snapshot."""
        market_info = MarketAnalyzer.characterize_market(snapshot.market)
        book_info = {}
        if snapshot.order_book:
            book_info = MarketAnalyzer.analyze_order_book(snapshot.order_book)

        return {
            "market": market_info,
            "order_book": book_info,
            "liquidity_score": snapshot.liquidity_score,
            "volume_24h": snapshot.volume_24h,
        }

    # ── Event Analysis ─────────────────────────────────────────────────

    @staticmethod
    def analyze_event(event: Event) -> dict:
        """Analyze an event and its constituent markets."""
        markets_data = [
            MarketAnalyzer.characterize_market(m) for m in event.markets
        ]
        total_volume = sum(m.volume for m in event.markets)
        total_liquidity = sum(m.liquidity for m in event.markets)

        return {
            "id": event.id,
            "title": event.title,
            "tradeable": event.is_tradeable,
            "market_count": len(event.markets),
            "total_volume": total_volume,
            "total_liquidity": total_liquidity,
            "markets": markets_data,
            "tags": event.tags,
        }

    # ── Comparative Analysis ───────────────────────────────────────────

    @staticmethod
    def rank_markets(
        markets: list[Market],
        by: str = "volume",
        descending: bool = True,
    ) -> list[Market]:
        """Rank markets by a given metric."""
        key_map = {
            "volume": lambda m: m.volume,
            "liquidity": lambda m: m.liquidity,
            "certainty": lambda m: abs((m.yes_price or 0.5) - 0.5),
            "uncertainty": lambda m: 1 - abs((m.yes_price or 0.5) - 0.5),
        }
        key_fn = key_map.get(by, key_map["volume"])
        return sorted(markets, key=key_fn, reverse=descending)

    @staticmethod
    def filter_markets(
        markets: list[Market],
        min_volume: float = 0,
        min_liquidity: float = 0,
        max_certainty: float = 1.0,
        categories: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
    ) -> list[Market]:
        """Filter markets by criteria."""
        result = []
        for m in markets:
            if m.volume < min_volume:
                continue
            if m.liquidity < min_liquidity:
                continue
            certainty = abs((m.yes_price or 0.5) - 0.5) * 2
            if certainty > max_certainty:
                continue
            if categories and m.category not in categories:
                continue
            if tags and not any(t in m.tags for t in tags):
                continue
            result.append(m)
        return result
