"""
Ms-MASA Agent Builder Example

Demonstrates how to use the agent builder toolkit to generate
custom Polymarket agents from templates.
"""

from ms_masa.builder.agent_builder import AgentBuilder
from ms_masa.builder.templates import AgentTemplates
from ms_masa.knowledge.polymarket_kb import PolymarketKB

# ── List Available Templates ───────────────────────────────────────
print("=== Available Agent Templates ===")
for name, desc in AgentTemplates.list_templates().items():
    print(f"  {name}: {desc}")

# ── List Agent Patterns ────────────────────────────────────────────
print("\n=== Agent Architecture Patterns ===")
for pattern_name, pattern in PolymarketKB.AGENT_PATTERNS.items():
    print(f"\n  {pattern_name}:")
    print(f"    Description: {pattern['description']}")
    print(f"    Requires: {pattern['requires']}")
    print(f"    Capabilities:")
    for cap in pattern['capabilities']:
        print(f"      - {cap}")

# ── Generate Agent Code ────────────────────────────────────────────
builder = AgentBuilder(output_dir="./generated_agents")

# Preview code without writing to disk
print("\n=== Market Monitor Agent (preview) ===")
code = builder.generate("market_monitor", write=False)
print(code[:500] + "...\n")

# ── Scaffold Complete Project ──────────────────────────────────────
print("=== Scaffold Preview ===")
files = builder.scaffold_project("my_polymarket_agent", agent_type="analytical_agent")
for path, content in files.items():
    print(f"  {path} ({len(content)} bytes)")

# To write to disk:
# created = builder.write_scaffold("my_polymarket_agent", agent_type="analytical_agent")
# for f in created:
#     print(f"  Created: {f}")

# ── Full Ecosystem Reference ──────────────────────────────────────
from ms_masa.knowledge.ecosystem import EcosystemReference
print("\n=== Ecosystem Summary ===")
print(EcosystemReference.summary())
