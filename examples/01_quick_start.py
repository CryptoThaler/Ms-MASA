"""
Ms-MASA Quick Start Example

Demonstrates basic agent usage for Polymarket platform knowledge
and market data access. No authentication required for read operations.
"""

from ms_masa import MsMasaAgent

# Initialize agent (no auth needed for read-only)
agent = MsMasaAgent()

# ── Knowledge Base ─────────────────────────────────────────────────
# Instant platform knowledge lookup (zero API calls)
print("=== Platform Overview ===")
platform = agent.explain("platform")
for key, val in platform.items():
    print(f"  {key}: {val}")

print("\n=== Available Topics ===")
from ms_masa.knowledge.polymarket_kb import PolymarketKB
for topic in PolymarketKB.topics():
    print(f"  - {topic}")

# ── Quick Reference Cards ──────────────────────────────────────────
print("\n=== CLOB API Reference ===")
print(agent.ref("clob_api"))

# ── Agent Context (for LLM consumption) ────────────────────────────
print("\n=== Compact Agent Context ===")
print(agent.get_agent_context("read_only_agent"))

# ── Live Market Data (requires internet) ───────────────────────────
# Uncomment to run against live API:
#
# print("\n=== Top Markets by Volume ===")
# markets = agent.scan_markets(limit=5, sort_by="volume")
# for m in markets:
#     print(f"  {m['question'][:60]} | Yes:{m['yes_price']} | Vol:{m['volume']:.0f}")
#
# print("\n=== Market Search ===")
# results = agent.search_markets("election", limit=3)
# for r in results:
#     print(f"  {r['question'][:60]} | Yes:{r['yes_price']}")

print("\n=== Agent Status ===")
status = agent.status()
for key, val in status.items():
    print(f"  {key}: {val}")
