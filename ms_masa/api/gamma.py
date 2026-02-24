"""
Gamma API client for Polymarket market discovery.

The Gamma API provides market metadata, event information, and
discovery endpoints. This is the primary interface for finding
markets and understanding their structure.

Endpoints:
    GET /markets       - List/filter markets
    GET /markets/{id}  - Single market detail
    GET /events        - List/filter events
    GET /events/{id}   - Single event detail

Query parameters:
    active (bool)       - Filter by active status
    closed (bool)       - Filter by closed status
    archived (bool)     - Filter by archived status
    limit (int)         - Results per page
    offset (int)        - Pagination offset
    order (str)         - Sort field
    ascending (bool)    - Sort direction
    tag (str)           - Filter by tag
    slug (str)          - Filter by slug
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx

from ms_masa.config import MsMasaConfig, PolymarketEndpoints
from ms_masa.models import Event, Market

logger = logging.getLogger(__name__)


class GammaClient:
    """Client for Polymarket's Gamma API (market discovery & metadata)."""

    def __init__(self, config: Optional[MsMasaConfig] = None):
        self._endpoints = (config or MsMasaConfig()).endpoints
        self._base = self._endpoints.gamma
        self._markets_url = self._endpoints.gamma_markets
        self._events_url = self._endpoints.gamma_events
        self._cache: dict[str, Any] = {}

    # ── Market Endpoints ───────────────────────────────────────────────

    def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: Optional[bool] = None,
        closed: Optional[bool] = None,
        archived: Optional[bool] = None,
        tag: Optional[str] = None,
        slug: Optional[str] = None,
        order: Optional[str] = None,
        ascending: bool = False,
    ) -> list[dict]:
        """Fetch markets from Gamma API with filters."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if active is not None:
            params["active"] = str(active).lower()
        if closed is not None:
            params["closed"] = str(closed).lower()
        if archived is not None:
            params["archived"] = str(archived).lower()
        if tag:
            params["tag"] = tag
        if slug:
            params["slug"] = slug
        if order:
            params["order"] = order
            params["ascending"] = str(ascending).lower()

        resp = httpx.get(self._markets_url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_market(self, market_id: str) -> dict:
        """Fetch a single market by ID."""
        url = f"{self._markets_url}/{market_id}"
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_tradeable_markets(self, limit: int = 100) -> list[Market]:
        """Fetch all currently tradeable markets as Market objects."""
        raw = self.get_markets(
            limit=limit,
            active=True,
            closed=False,
            archived=False,
        )
        return [self._parse_market(m) for m in raw if m.get("enableOrderBook")]

    def get_all_tradeable_markets(self) -> list[Market]:
        """Paginate through all tradeable markets."""
        all_markets: list[Market] = []
        offset = 0
        limit = 100
        while True:
            raw = self.get_markets(
                limit=limit,
                offset=offset,
                active=True,
                closed=False,
                archived=False,
            )
            if not raw:
                break
            tradeable = [self._parse_market(m) for m in raw if m.get("enableOrderBook")]
            all_markets.extend(tradeable)
            if len(raw) < limit:
                break
            offset += limit
        return all_markets

    # ── Event Endpoints ────────────────────────────────────────────────

    def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        active: Optional[bool] = None,
        closed: Optional[bool] = None,
        archived: Optional[bool] = None,
        tag: Optional[str] = None,
        slug: Optional[str] = None,
    ) -> list[dict]:
        """Fetch events from Gamma API with filters."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if active is not None:
            params["active"] = str(active).lower()
        if closed is not None:
            params["closed"] = str(closed).lower()
        if archived is not None:
            params["archived"] = str(archived).lower()
        if tag:
            params["tag"] = tag
        if slug:
            params["slug"] = slug

        resp = httpx.get(self._events_url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_event(self, event_id: str) -> dict:
        """Fetch a single event by ID."""
        url = f"{self._events_url}/{event_id}"
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_tradeable_events(self, limit: int = 100) -> list[Event]:
        """Fetch active, non-restricted events with their markets."""
        raw = self.get_events(
            limit=limit,
            active=True,
            closed=False,
            archived=False,
        )
        return [
            self._parse_event(e) for e in raw
            if not e.get("restricted", False)
        ]

    # ── Parsing ────────────────────────────────────────────────────────

    @staticmethod
    def _parse_market(data: dict) -> Market:
        """Convert raw Gamma API market response to Market model."""
        outcome_prices = []
        raw_prices = data.get("outcomePrices", "[]")
        if isinstance(raw_prices, str):
            try:
                outcome_prices = [float(p) for p in json.loads(raw_prices)]
            except (json.JSONDecodeError, ValueError):
                pass
        elif isinstance(raw_prices, list):
            outcome_prices = [float(p) for p in raw_prices]

        clob_ids = []
        raw_ids = data.get("clobTokenIds", "[]")
        if isinstance(raw_ids, str):
            try:
                clob_ids = json.loads(raw_ids)
            except json.JSONDecodeError:
                pass
        elif isinstance(raw_ids, list):
            clob_ids = raw_ids

        tags = []
        if data.get("tags"):
            if isinstance(data["tags"], list):
                tags = [
                    t.get("label", t) if isinstance(t, dict) else str(t)
                    for t in data["tags"]
                ]

        return Market(
            id=str(data.get("id", "")),
            question=data.get("question", ""),
            description=data.get("description", ""),
            condition_id=data.get("conditionId", ""),
            slug=data.get("slug", ""),
            status=data.get("status", "active"),
            outcomes=data.get("outcomes", ["Yes", "No"]),
            outcome_prices=outcome_prices,
            clob_token_ids=clob_ids,
            volume=float(data.get("volume", 0)),
            liquidity=float(data.get("liquidity", 0)),
            end_date=data.get("endDate", ""),
            category=data.get("category", ""),
            neg_risk=data.get("negRisk", False),
            enable_order_book=data.get("enableOrderBook", True),
            active=data.get("active", True),
            closed=data.get("closed", False),
            archived=data.get("archived", False),
            tags=tags,
        )

    @staticmethod
    def _parse_event(data: dict) -> Event:
        """Convert raw Gamma API event response to Event model."""
        markets = []
        for m in data.get("markets", []):
            markets.append(GammaClient._parse_market(m))

        tags = []
        if data.get("tags"):
            if isinstance(data["tags"], list):
                tags = [
                    t.get("label", t) if isinstance(t, dict) else str(t)
                    for t in data["tags"]
                ]

        return Event(
            id=str(data.get("id", "")),
            title=data.get("title", ""),
            description=data.get("description", ""),
            slug=data.get("slug", ""),
            markets=markets,
            active=data.get("active", True),
            closed=data.get("closed", False),
            archived=data.get("archived", False),
            restricted=data.get("restricted", False),
            tags=tags,
        )
