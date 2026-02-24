"""
Core data models for the Ms-MASA agent system.
Pydantic models mirroring Polymarket's data structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Enums ──────────────────────────────────────────────────────────────

class OrderType(str, Enum):
    GTC = "GTC"   # Good-Till-Cancelled
    FOK = "FOK"   # Fill-or-Kill
    GTD = "GTD"   # Good-Till-Date
    FAK = "FAK"   # Fill-and-Kill


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class AssetType(str, Enum):
    COLLATERAL = "COLLATERAL"
    CONDITIONAL = "CONDITIONAL"


class MarketStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"
    RESOLVED = "resolved"


class SignatureType(int, Enum):
    EOA = 0       # Standard wallet (MetaMask, hardware)
    POLY_PROXY = 1  # Email/Magic wallet
    POLY_GNOSIS = 2  # Browser wallet proxy


# ── Market Data Models ─────────────────────────────────────────────────

@dataclass
class TickSize:
    """Valid tick sizes for Polymarket order books."""
    DIME: str = "0.1"
    CENT: str = "0.01"
    TENTH_CENT: str = "0.001"
    BASIS_POINT: str = "0.0001"


@dataclass
class OrderBookLevel:
    price: float
    size: float


@dataclass
class OrderBook:
    market: str = ""
    asset_id: str = ""
    timestamp: str = ""
    bids: list[OrderBookLevel] = field(default_factory=list)
    asks: list[OrderBookLevel] = field(default_factory=list)
    min_order_size: float = 0.0
    tick_size: str = "0.01"
    last_trade_price: float = 0.0
    neg_risk: bool = False
    spread: float = 0.0
    midpoint: float = 0.0
    depth_bid: float = 0.0
    depth_ask: float = 0.0

    def __post_init__(self):
        if self.bids and self.asks:
            best_bid = max(b.price for b in self.bids)
            best_ask = min(a.price for a in self.asks)
            self.spread = round(best_ask - best_bid, 6)
            self.midpoint = round((best_bid + best_ask) / 2, 6)
            self.depth_bid = sum(b.size for b in self.bids)
            self.depth_ask = sum(a.size for a in self.asks)


@dataclass
class Market:
    """Represents a Polymarket prediction market."""
    id: str = ""
    question: str = ""
    description: str = ""
    condition_id: str = ""
    slug: str = ""
    status: str = "active"
    outcomes: list[str] = field(default_factory=lambda: ["Yes", "No"])
    outcome_prices: list[float] = field(default_factory=list)
    clob_token_ids: list[str] = field(default_factory=list)
    volume: float = 0.0
    liquidity: float = 0.0
    end_date: str = ""
    category: str = ""
    neg_risk: bool = False
    enable_order_book: bool = True
    active: bool = True
    closed: bool = False
    archived: bool = False
    tags: list[str] = field(default_factory=list)

    @property
    def is_tradeable(self) -> bool:
        return self.active and not self.closed and not self.archived and self.enable_order_book

    @property
    def yes_price(self) -> Optional[float]:
        return self.outcome_prices[0] if self.outcome_prices else None

    @property
    def no_price(self) -> Optional[float]:
        return self.outcome_prices[1] if len(self.outcome_prices) > 1 else None

    @property
    def yes_token(self) -> Optional[str]:
        return self.clob_token_ids[0] if self.clob_token_ids else None

    @property
    def no_token(self) -> Optional[str]:
        return self.clob_token_ids[1] if len(self.clob_token_ids) > 1 else None


@dataclass
class Event:
    """Represents a Polymarket event (groups multiple markets)."""
    id: str = ""
    title: str = ""
    description: str = ""
    slug: str = ""
    markets: list[Market] = field(default_factory=list)
    active: bool = True
    closed: bool = False
    archived: bool = False
    restricted: bool = False
    tags: list[str] = field(default_factory=list)

    @property
    def is_tradeable(self) -> bool:
        return self.active and not self.closed and not self.archived and not self.restricted


# ── Order Models ───────────────────────────────────────────────────────

@dataclass
class OrderArgs:
    token_id: str = ""
    price: float = 0.0
    size: float = 0.0
    side: str = "BUY"
    fee_rate_bps: Optional[int] = None
    nonce: Optional[int] = None
    expiration: Optional[int] = None


@dataclass
class MarketOrderArgs:
    token_id: str = ""
    amount: float = 0.0
    side: str = "BUY"
    price: Optional[float] = None
    fee_rate_bps: Optional[int] = None
    nonce: Optional[int] = None


@dataclass
class Trade:
    market_id: str = ""
    token_id: str = ""
    side: str = ""
    price: float = 0.0
    size: float = 0.0
    timestamp: str = ""
    order_type: str = "GTC"


# ── API Credentials ───────────────────────────────────────────────────

@dataclass
class ApiCreds:
    api_key: str = ""
    api_secret: str = ""
    api_passphrase: str = ""


# ── Agent Models ───────────────────────────────────────────────────────

@dataclass
class AgentCapability:
    """Defines a capability that an agent possesses."""
    name: str = ""
    description: str = ""
    module: str = ""
    enabled: bool = True


@dataclass
class AgentProfile:
    """Agent configuration profile."""
    name: str = "Ms-MASA"
    version: str = "0.1.0"
    capabilities: list[AgentCapability] = field(default_factory=list)
    max_context_tokens: int = 4096
    market_focus: list[str] = field(default_factory=list)
    risk_parameters: dict = field(default_factory=dict)


# ── Analysis Models ───────────────────────────────────────────────────

@dataclass
class MarketSnapshot:
    """Point-in-time snapshot of market state for analysis."""
    market: Market = field(default_factory=Market)
    order_book: Optional[OrderBook] = None
    volume_24h: float = 0.0
    price_change_24h: float = 0.0
    liquidity_score: float = 0.0
    volatility: float = 0.0
    timestamp: str = ""


@dataclass
class MarketSignal:
    """Signal generated from market analysis."""
    market_id: str = ""
    signal_type: str = ""  # e.g., "liquidity_gap", "momentum", "spread_opportunity"
    strength: float = 0.0  # -1.0 to 1.0
    description: str = ""
    metadata: dict = field(default_factory=dict)
