"""Tests for ms_masa.analysis.signals."""

from ms_masa.analysis.signals import SignalEngine
from ms_masa.models import Market, MarketSnapshot, OrderBook, OrderBookLevel


def _snap(yes_price=0.5, bids=None, asks=None, market_id="m1"):
    book = None
    if bids is not None or asks is not None:
        book = OrderBook(bids=bids or [], asks=asks or [])
    return MarketSnapshot(
        market=Market(id=market_id, outcome_prices=[yes_price, 1 - yes_price]),
        order_book=book,
    )


def test_no_signals_for_normal_market():
    engine = SignalEngine()
    snap = _snap(
        yes_price=0.6,
        bids=[OrderBookLevel(0.58, 5000)],
        asks=[OrderBookLevel(0.62, 5000)],
    )
    signals = engine.generate_signals(snap)
    assert len(signals) == 0


def test_wide_spread_signal():
    engine = SignalEngine(spread_threshold=0.05)
    snap = _snap(
        yes_price=0.5,
        bids=[OrderBookLevel(0.40, 100)],
        asks=[OrderBookLevel(0.60, 100)],
    )
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "wide_spread" in types


def test_imbalance_bid_heavy():
    engine = SignalEngine(imbalance_threshold=0.3)
    snap = _snap(
        yes_price=0.6,
        bids=[OrderBookLevel(0.59, 1000)],
        asks=[OrderBookLevel(0.61, 100)],
    )
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "imbalance_bid_heavy" in types


def test_imbalance_ask_heavy():
    engine = SignalEngine(imbalance_threshold=0.3)
    snap = _snap(
        yes_price=0.6,
        bids=[OrderBookLevel(0.59, 100)],
        asks=[OrderBookLevel(0.61, 1000)],
    )
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "imbalance_ask_heavy" in types


def test_low_liquidity_signal():
    engine = SignalEngine(low_liquidity_threshold=1000)
    snap = _snap(
        yes_price=0.6,
        bids=[OrderBookLevel(0.59, 50)],
        asks=[OrderBookLevel(0.61, 50)],
    )
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "low_liquidity" in types


def test_near_certainty_signal():
    engine = SignalEngine()
    snap = _snap(yes_price=0.97)
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "near_certainty" in types


def test_near_certainty_low():
    engine = SignalEngine()
    snap = _snap(yes_price=0.03)
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "near_certainty" in types


def test_high_uncertainty_signal():
    engine = SignalEngine()
    snap = _snap(yes_price=0.50)
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "high_uncertainty" in types


def test_no_uncertainty_signal_at_60():
    engine = SignalEngine()
    snap = _snap(yes_price=0.60)
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "high_uncertainty" not in types


def test_scan_snapshots():
    engine = SignalEngine()
    snaps = [
        _snap(yes_price=0.50, market_id="m1"),  # high_uncertainty
        _snap(yes_price=0.70, market_id="m2"),  # no signals
        _snap(yes_price=0.98, market_id="m3"),  # near_certainty
    ]
    result = engine.scan_snapshots(snaps)
    assert "m1" in result
    assert "m2" not in result
    assert "m3" in result


def test_signal_strength_range():
    engine = SignalEngine(spread_threshold=0.01)
    snap = _snap(
        yes_price=0.50,
        bids=[OrderBookLevel(0.30, 10)],
        asks=[OrderBookLevel(0.70, 10)],
    )
    signals = engine.generate_signals(snap)
    for s in signals:
        assert -1.0 <= s.strength <= 1.0


def test_no_book_signals_without_book():
    engine = SignalEngine()
    snap = _snap(yes_price=0.50)
    signals = engine.generate_signals(snap)
    # Should only have price signals, not book signals
    types = [s.signal_type for s in signals]
    assert "wide_spread" not in types
    assert "low_liquidity" not in types


# ── New Signal Type Tests ─────────────────────────────────────────────


def test_price_momentum_up():
    engine = SignalEngine()
    snap = _snap(yes_price=0.70)
    snap.price_change_24h = 0.10
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "price_momentum" in types
    momentum = [s for s in signals if s.signal_type == "price_momentum"][0]
    assert momentum.strength > 0
    assert momentum.metadata["direction"] == "up"


def test_price_momentum_down():
    engine = SignalEngine()
    snap = _snap(yes_price=0.30)
    snap.price_change_24h = -0.10
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "price_momentum" in types
    momentum = [s for s in signals if s.signal_type == "price_momentum"][0]
    assert momentum.strength < 0


def test_no_momentum_for_small_change():
    engine = SignalEngine()
    snap = _snap(yes_price=0.50)
    snap.price_change_24h = 0.02  # below 0.05 threshold
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "price_momentum" not in types


def test_volume_spike():
    engine = SignalEngine()
    snap = _snap(yes_price=0.60)
    snap.market.volume = 10000
    snap.volume_24h = 5000  # 50% of total in 24h
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "volume_spike" in types


def test_no_volume_spike_for_low_volume():
    engine = SignalEngine()
    snap = _snap(yes_price=0.60)
    snap.market.volume = 10000
    snap.volume_24h = 500  # only 5% of total
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "volume_spike" not in types


def test_uncertainty_shift_increasing():
    engine = SignalEngine()
    # Price moved from 0.70 to 0.55 (toward 50%, uncertainty increasing)
    snap = _snap(yes_price=0.55)
    snap.price_change_24h = -0.15
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "uncertainty_shift" in types
    shift = [s for s in signals if s.signal_type == "uncertainty_shift"][0]
    assert shift.metadata["direction"] == "increasing"


def test_uncertainty_shift_decreasing():
    engine = SignalEngine()
    # Price moved from 0.60 to 0.80 (away from 50%, uncertainty decreasing)
    snap = _snap(yes_price=0.80)
    snap.price_change_24h = 0.20
    signals = engine.generate_signals(snap)
    types = [s.signal_type for s in signals]
    assert "uncertainty_shift" in types
    shift = [s for s in signals if s.signal_type == "uncertainty_shift"][0]
    assert shift.metadata["direction"] == "decreasing"
