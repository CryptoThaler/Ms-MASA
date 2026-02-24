"""
Ms-MASA Reference Cards Example

Demonstrates the quick reference system designed for minimal token
usage when agents need operational guidance.
"""

from ms_masa.knowledge.reference import QuickReference

# ── Individual Reference Cards ─────────────────────────────────────

print("=" * 60)
print(QuickReference.gamma_api())

print("\n" + "=" * 60)
print(QuickReference.clob_api())

print("\n" + "=" * 60)
print(QuickReference.order_flow())

print("\n" + "=" * 60)
print(QuickReference.auth_setup())

print("\n" + "=" * 60)
print(QuickReference.agent_architecture())

print("\n" + "=" * 60)
print(QuickReference.market_concepts())

# ── Full Knowledge Base Lookup ─────────────────────────────────────

from ms_masa.knowledge.polymarket_kb import PolymarketKB

print("\n\n=== Knowledge Base: Smart Contracts ===")
import json
contracts = PolymarketKB.lookup("contracts")
print(json.dumps(contracts, indent=2))

print("\n=== Knowledge Base: SDK Methods ===")
sdks = PolymarketKB.lookup("sdks")
for sdk_name, sdk_info in sdks.items():
    print(f"\n  {sdk_name}:")
    if "install" in sdk_info:
        print(f"    Install: {sdk_info['install']}")
    print(f"    Purpose: {sdk_info['purpose']}")
    if "key_methods" in sdk_info:
        print(f"    Methods ({len(sdk_info['key_methods'])}):")
        for m in sdk_info["key_methods"][:5]:
            print(f"      - {m}")
        if len(sdk_info["key_methods"]) > 5:
            print(f"      ... and {len(sdk_info['key_methods'])-5} more")

# ── Compact Agent Context (for LLM prompts) ────────────────────────

print("\n=== Agent Context Strings ===")
for agent_type in ["read_only_agent", "analytical_agent", "trading_agent"]:
    print(f"\n--- {agent_type} ---")
    print(PolymarketKB.get_agent_context(agent_type))
