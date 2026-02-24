"""
CLOB (Central Limit Order Book) client for Polymarket.

The CLOB API provides order book data, price feeds, and authenticated
trading operations. It runs on Polygon (chain_id=137).

Public Endpoints (no auth):
    GET /          - Health check
    GET /time      - Server time
    GET /midpoint  - Midpoint price for a token
    GET /price     - Best price for side
    GET /book      - Order book for token
    GET /books     - Multiple order books
    GET /markets   - Simplified market list
    GET /last-trade-price - Last executed trade price

Authenticated Endpoints:
    POST /order    - Place an order
    DELETE /order  - Cancel an order
    DELETE /orders - Cancel all orders
    GET /orders    - List open orders
    GET /trades    - Trade history

Authentication Levels:
    L0: Public (no credentials)
    L1: API key + secret + passphrase (derived from wallet signature)
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from ms_masa.config import MsMasaConfig
from ms_masa.models import OrderBook, OrderBookLevel

logger = logging.getLogger(__name__)


class ClobClient:
    """Client for Polymarket's CLOB API (order book & trading)."""

    def __init__(self, config: Optional[MsMasaConfig] = None):
        self._config = config or MsMasaConfig()
        self._base = self._config.endpoints.clob
        self._timeout = 30

    # ── Public Endpoints (L0) ──────────────────────────────────────────

    def health(self) -> bool:
        """Check if the CLOB API is healthy."""
        try:
            resp = httpx.get(f"{self._base}/", timeout=self._timeout)
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def server_time(self) -> str:
        """Get CLOB server timestamp."""
        resp = httpx.get(f"{self._base}/time", timeout=self._timeout)
        resp.raise_for_status()
        return resp.text

    def get_midpoint(self, token_id: str) -> float:
        """Get midpoint price for a token (0.00 - 1.00)."""
        resp = httpx.get(
            f"{self._base}/midpoint",
            params={"token_id": token_id},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("mid", 0.0))

    def get_price(self, token_id: str, side: str = "BUY") -> float:
        """Get best available price for a side (BUY/SELL)."""
        resp = httpx.get(
            f"{self._base}/price",
            params={"token_id": token_id, "side": side},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("price", 0.0))

    def get_order_book(self, token_id: str) -> OrderBook:
        """Get full order book for a token."""
        resp = httpx.get(
            f"{self._base}/book",
            params={"token_id": token_id},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return self._parse_order_book(resp.json())

    def get_order_books(self, token_ids: list[str]) -> list[OrderBook]:
        """Get order books for multiple tokens in one call."""
        params = [{"token_id": tid} for tid in token_ids]
        resp = httpx.get(
            f"{self._base}/books",
            params={"params": params},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return [self._parse_order_book(b) for b in resp.json()]

    def get_simplified_markets(self) -> list[dict]:
        """Get simplified market list from CLOB."""
        resp = httpx.get(
            f"{self._base}/simplified-markets",
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def get_last_trade_price(self, token_id: str) -> float:
        """Get the last executed trade price for a token."""
        resp = httpx.get(
            f"{self._base}/last-trade-price",
            params={"token_id": token_id},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("price", 0.0))

    # ── Authenticated Endpoints (L1) ──────────────────────────────────

    def get_open_orders(
        self,
        headers: dict[str, str],
        market: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> list[dict]:
        """Get open orders (requires L1 auth headers)."""
        params: dict[str, Any] = {}
        if market:
            params["market"] = market
        if asset_id:
            params["asset_id"] = asset_id

        resp = httpx.get(
            f"{self._base}/orders",
            params=params,
            headers=headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def get_trades(
        self,
        headers: dict[str, str],
        market: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> list[dict]:
        """Get trade history (requires L1 auth headers)."""
        params: dict[str, Any] = {}
        if market:
            params["market"] = market
        if before:
            params["before"] = before
        if after:
            params["after"] = after

        resp = httpx.get(
            f"{self._base}/trades",
            params=params,
            headers=headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Parsing ────────────────────────────────────────────────────────

    @staticmethod
    def _parse_order_book(data: dict) -> OrderBook:
        """Parse raw order book JSON into OrderBook model."""
        bids = [
            OrderBookLevel(price=float(b.get("price", 0)), size=float(b.get("size", 0)))
            for b in data.get("bids", [])
        ]
        asks = [
            OrderBookLevel(price=float(a.get("price", 0)), size=float(a.get("size", 0)))
            for a in data.get("asks", [])
        ]
        return OrderBook(
            market=data.get("market", ""),
            asset_id=data.get("asset_id", ""),
            timestamp=data.get("timestamp", ""),
            bids=bids,
            asks=asks,
            min_order_size=float(data.get("min_order_size", 0)),
            tick_size=data.get("tick_size", "0.01"),
            last_trade_price=float(data.get("last_trade_price", 0)),
            neg_risk=data.get("neg_risk", False),
        )
