"""Tests for ms_masa.analysis.market_analyzer."""

from ms_masa.analysis.market_analyzer import MarketAnalyzer
from ms_masa.models import (
    Event,
    Market,
    MarketSnapshot,
    OrderBook,
    OrderBookLevel,
)


def _make_book(bids=None, asks=None):
    return OrderBook(
        bids=bids or [],
        asks=asks or [],
    )


def _make_market(**kwargs):
    defaults = {
        "id": "test-market",
        "question": "Will it rain?",
        "outcome_prices": [0.6, 0.4],
        "volume": 50000,
        "liquidity": 10000,
    }
    defaults.update(kwargs)
    return Market(**defaults)


# ── Order Book Analysis ───────────────────────────────────────────────


def test_analyze_empty_book():
    book = _make_book()
    result = MarketAnalyzer.analyze_order_book(book)
    assert result["status"] == "empty"
    assert result["tradeable"] is False


def test_analyze_order_book():
    book = _make_book(
        bids=[OrderBookLevel(0.50, 100), OrderBookLevel(0.49, 200)],
        asks=[OrderBookLevel(0.55, 150), OrderBookLevel(0.56, 50)],
    )
    result = MarketAnalyzer.analyze_order_book(book)
    assert result["status"] == "active"
    assert result["tradeable"] is True
    assert result["best_bid"] == 0.50
    assert result["best_ask"] == 0.55
    assert result["spread"] == 0.05
    assert result["midpoint"] == 0.525
    assert result["bid_depth"] == 300
    assert result["ask_depth"] == 200
    assert result["bid_levels"] == 2
    assert result["ask_levels"] == 2
    # Imbalance: (300-200)/500 = 0.2
    assert abs(result["imbalance"] - 0.2) < 0.001


def test_analyze_book_concentration():
    book = _make_book(
        bids=[OrderBookLevel(0.50, 100)],
        asks=[OrderBookLevel(0.55, 100)],
    )
    result = MarketAnalyzer.analyze_order_book(book)
    # With single level, top3 concentration = 1.0
    assert result["bid_top3_concentration"] == 1.0
    assert result["ask_top3_concentration"] == 1.0


# ── Market Characterization ──────────────────────────────────────────


def test_characterize_market():
    m = _make_market()
    result = MarketAnalyzer.characterize_market(m)
    assert result["id"] == "test-market"
    assert result["question"] == "Will it rain?"
    assert result["yes_price"] == 0.6
    assert result["volume"] == 50000
    # certainty = |0.6 - 0.5| * 2 = 0.2
    assert abs(result["certainty"] - 0.2) < 0.001


def test_characterize_market_no_price():
    m = _make_market(outcome_prices=[])
    result = MarketAnalyzer.characterize_market(m)
    assert result["yes_price"] == 0.5  # default


# ── Snapshot Analysis ─────────────────────────────────────────────────


def test_analyze_snapshot_without_book():
    snap = MarketSnapshot(market=_make_market())
    result = MarketAnalyzer.analyze_snapshot(snap)
    assert "market" in result
    assert result["order_book"] == {}


def test_analyze_snapshot_with_book():
    book = _make_book(
        bids=[OrderBookLevel(0.50, 100)],
        asks=[OrderBookLevel(0.55, 100)],
    )
    snap = MarketSnapshot(market=_make_market(), order_book=book)
    result = MarketAnalyzer.analyze_snapshot(snap)
    assert result["order_book"]["status"] == "active"


# ── Event Analysis ────────────────────────────────────────────────────


def test_analyze_event():
    m1 = _make_market(id="m1", volume=1000, liquidity=500)
    m2 = _make_market(id="m2", volume=2000, liquidity=800)
    event = Event(id="e1", title="Test Event", markets=[m1, m2])

    result = MarketAnalyzer.analyze_event(event)
    assert result["market_count"] == 2
    assert result["total_volume"] == 3000
    assert result["total_liquidity"] == 1300


# ── Ranking ───────────────────────────────────────────────────────────


def test_rank_by_volume():
    m1 = _make_market(volume=100)
    m2 = _make_market(volume=500)
    m3 = _make_market(volume=200)
    ranked = MarketAnalyzer.rank_markets([m1, m2, m3], by="volume")
    assert [m.volume for m in ranked] == [500, 200, 100]


def test_rank_by_uncertainty():
    m_certain = _make_market(outcome_prices=[0.95, 0.05])
    m_uncertain = _make_market(outcome_prices=[0.50, 0.50])
    ranked = MarketAnalyzer.rank_markets([m_certain, m_uncertain], by="uncertainty")
    assert ranked[0].yes_price == 0.50  # most uncertain first


# ── Filtering ─────────────────────────────────────────────────────────


def test_filter_by_volume():
    m1 = _make_market(volume=100)
    m2 = _make_market(volume=1000)
    result = MarketAnalyzer.filter_markets([m1, m2], min_volume=500)
    assert len(result) == 1
    assert result[0].volume == 1000


def test_filter_by_liquidity():
    m1 = _make_market(liquidity=50)
    m2 = _make_market(liquidity=500)
    result = MarketAnalyzer.filter_markets([m1, m2], min_liquidity=100)
    assert len(result) == 1


def test_filter_by_certainty():
    m_certain = _make_market(outcome_prices=[0.98, 0.02])
    m_uncertain = _make_market(outcome_prices=[0.55, 0.45])
    result = MarketAnalyzer.filter_markets([m_certain, m_uncertain], max_certainty=0.5)
    assert len(result) == 1
    assert result[0].yes_price == 0.55


def test_filter_by_category():
    m1 = _make_market(category="politics")
    m2 = _make_market(category="sports")
    result = MarketAnalyzer.filter_markets([m1, m2], categories=["politics"])
    assert len(result) == 1


def test_filter_by_tags():
    m1 = _make_market(tags=["crypto", "defi"])
    m2 = _make_market(tags=["sports"])
    result = MarketAnalyzer.filter_markets([m1, m2], tags=["crypto"])
    assert len(result) == 1
