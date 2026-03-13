"""Tests for ms_masa.models data classes."""

from ms_masa.models import (
    AgentCapability,
    AgentProfile,
    AssetType,
    Event,
    Market,
    MarketOrderArgs,
    MarketSignal,
    MarketSnapshot,
    MarketStatus,
    OrderArgs,
    OrderBook,
    OrderBookLevel,
    OrderType,
    Side,
    SignatureType,
    TickSize,
    Trade,
)


# ── Enum Tests ────────────────────────────────────────────────────────


def test_order_type_values():
    assert OrderType.GTC == "GTC"
    assert OrderType.FOK == "FOK"
    assert OrderType.GTD == "GTD"
    assert OrderType.FAK == "FAK"


def test_side_values():
    assert Side.BUY == "BUY"
    assert Side.SELL == "SELL"


def test_asset_type_values():
    assert AssetType.COLLATERAL == "COLLATERAL"
    assert AssetType.CONDITIONAL == "CONDITIONAL"


def test_market_status_values():
    assert MarketStatus.ACTIVE == "active"
    assert MarketStatus.RESOLVED == "resolved"


def test_signature_type_values():
    assert SignatureType.EOA == 0
    assert SignatureType.POLY_PROXY == 1
    assert SignatureType.POLY_GNOSIS == 2


# ── OrderBook Tests ───────────────────────────────────────────────────


def test_order_book_empty():
    book = OrderBook()
    assert book.spread == 0.0
    assert book.midpoint == 0.0
    assert book.depth_bid == 0.0
    assert book.depth_ask == 0.0


def test_order_book_computed_fields():
    book = OrderBook(
        bids=[OrderBookLevel(0.45, 100), OrderBookLevel(0.44, 200)],
        asks=[OrderBookLevel(0.55, 150), OrderBookLevel(0.56, 50)],
    )
    assert book.spread == round(0.55 - 0.45, 6)
    assert book.midpoint == round((0.45 + 0.55) / 2, 6)
    assert book.depth_bid == 300.0
    assert book.depth_ask == 200.0


# ── Market Tests ──────────────────────────────────────────────────────


def test_market_defaults():
    m = Market()
    assert m.outcomes == ["Yes", "No"]
    assert m.is_tradeable is True
    assert m.yes_price is None
    assert m.no_price is None


def test_market_is_tradeable():
    m = Market(active=True, closed=False, archived=False, enable_order_book=True)
    assert m.is_tradeable is True

    m_closed = Market(active=True, closed=True)
    assert m_closed.is_tradeable is False

    m_archived = Market(active=True, archived=True)
    assert m_archived.is_tradeable is False


def test_market_prices():
    m = Market(outcome_prices=[0.7, 0.3], clob_token_ids=["tok1", "tok2"])
    assert m.yes_price == 0.7
    assert m.no_price == 0.3
    assert m.yes_token == "tok1"
    assert m.no_token == "tok2"


def test_market_single_outcome():
    m = Market(outcome_prices=[0.8])
    assert m.yes_price == 0.8
    assert m.no_price is None


# ── Event Tests ───────────────────────────────────────────────────────


def test_event_defaults():
    e = Event()
    assert e.is_tradeable is True
    assert e.markets == []


def test_event_not_tradeable():
    e = Event(restricted=True)
    assert e.is_tradeable is False


# ── MarketSignal Tests ────────────────────────────────────────────────


def test_market_signal_defaults():
    s = MarketSignal()
    assert s.strength == 0.0
    assert s.metadata == {}


def test_market_signal_populated():
    s = MarketSignal(
        market_id="abc",
        signal_type="wide_spread",
        strength=0.8,
        description="Spread is wide",
        metadata={"spread": 0.12},
    )
    assert s.signal_type == "wide_spread"
    assert s.metadata["spread"] == 0.12


# ── MarketSnapshot Tests ──────────────────────────────────────────────


def test_snapshot_defaults():
    snap = MarketSnapshot()
    assert snap.order_book is None
    assert snap.volume_24h == 0.0


# ── Agent Models ──────────────────────────────────────────────────────


def test_agent_capability():
    cap = AgentCapability(name="test", description="testing", module="mod")
    assert cap.enabled is True


def test_agent_profile():
    prof = AgentProfile()
    assert prof.name == "Ms-MASA"
    assert prof.version == "0.1.0"


# ── Order Models ──────────────────────────────────────────────────────


def test_order_args():
    o = OrderArgs(token_id="tok1", price=0.5, size=10, side="BUY")
    assert o.price == 0.5


def test_market_order_args():
    o = MarketOrderArgs(token_id="tok1", amount=100, side="BUY")
    assert o.amount == 100


def test_trade():
    t = Trade(market_id="m1", token_id="t1", side="BUY", price=0.5, size=10)
    assert t.order_type == "GTC"
