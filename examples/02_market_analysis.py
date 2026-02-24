"""
Ms-MASA Market Analysis Example

Demonstrates market analysis capabilities including order book
analysis, signal detection, and market characterization.
"""

from ms_masa import MsMasaAgent
from ms_masa.analysis.market_analyzer import MarketAnalyzer
from ms_masa.analysis.signals import SignalEngine
from ms_masa.models import Market, OrderBook, OrderBookLevel, MarketSnapshot

# ── Offline Analysis Demo ──────────────────────────────────────────
# Demonstrate analysis with synthetic data (no API calls needed)

sample_market = Market(
    id="sample-001",
    question="Will BTC exceed $100k by end of 2025?",
    outcomes=["Yes", "No"],
    outcome_prices=[0.65, 0.35],
    clob_token_ids=["token-yes", "token-no"],
    volume=1500000,
    liquidity=250000,
    category="crypto",
    neg_risk=False,
)

sample_book = OrderBook(
    bids=[
        OrderBookLevel(price=0.64, size=5000),
        OrderBookLevel(price=0.63, size=8000),
        OrderBookLevel(price=0.62, size=12000),
        OrderBookLevel(price=0.60, size=20000),
    ],
    asks=[
        OrderBookLevel(price=0.66, size=4000),
        OrderBookLevel(price=0.67, size=7000),
        OrderBookLevel(price=0.68, size=10000),
        OrderBookLevel(price=0.70, size=15000),
    ],
)

# Analyze market characteristics
analyzer = MarketAnalyzer()
print("=== Market Characterization ===")
char = analyzer.characterize_market(sample_market)
for k, v in char.items():
    print(f"  {k}: {v}")

# Analyze order book
print("\n=== Order Book Analysis ===")
book_analysis = analyzer.analyze_order_book(sample_book)
for k, v in book_analysis.items():
    print(f"  {k}: {v}")

# Generate signals
snapshot = MarketSnapshot(
    market=sample_market,
    order_book=sample_book,
    volume_24h=1500000,
    liquidity_score=0.75,
)

engine = SignalEngine()
print("\n=== Detected Signals ===")
signals = engine.generate_signals(snapshot)
for sig in signals:
    print(f"  [{sig.signal_type}] strength={sig.strength:.2f} - {sig.description}")

# Full snapshot analysis
print("\n=== Full Snapshot Analysis ===")
full = analyzer.analyze_snapshot(snapshot)
import json
print(json.dumps(full, indent=2, default=str))

# ── Live Analysis (uncomment to use) ───────────────────────────────
# agent = MsMasaAgent()
# analysis = agent.analyze_market("your-market-id")
# print(json.dumps(analysis, indent=2))
#
# signals = agent.detect_signals(limit=20)
# for mid, sigs in signals.items():
#     print(f"Market {mid}: {len(sigs)} signals")
