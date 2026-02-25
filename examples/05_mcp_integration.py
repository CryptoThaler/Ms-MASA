"""
Example 5: MCP Integration

Shows how Ms-MASA exposes itself as an MCP server, and how to
use the skill manifest for agent marketplace integration.
"""

from ms_masa.mcp_server import TOOLS, execute_tool
from ms_masa.skill_manifest import MANIFEST


def demo_mcp_tools():
    """Show all MCP tools available."""
    print("=== Ms-MASA MCP Tools ===\n")
    for tool in TOOLS:
        print(f"  {tool['name']}")
        print(f"    {tool['description'][:80]}...")
        params = tool["inputSchema"].get("properties", {})
        if params:
            print(f"    Params: {', '.join(params.keys())}")
        print()


def demo_tool_execution():
    """Execute MCP tools directly (what happens when Claude calls them)."""
    print("=== Direct Tool Execution ===\n")

    # Knowledge lookup (no API needed)
    result = execute_tool("polymarket_explain", {"topic": "platform"})
    print(f"polymarket_explain('platform'):")
    print(f"  Type: {result.get('type', 'N/A')}")
    print(f"  Chain: {result.get('chain', 'N/A')}")
    print()

    # Reference card
    result = execute_tool("polymarket_reference", {"card": "market_concepts"})
    print(f"polymarket_reference('market_concepts'):")
    print(f"  {result[:100]}...")
    print()

    # Agent context
    result = execute_tool("polymarket_agent_context", {"agent_type": "analytical_agent"})
    print(f"polymarket_agent_context('analytical_agent'):")
    print(f"  {result[:120]}...")
    print()


def demo_skill_manifest():
    """Show the skill manifest for marketplace registration."""
    print("=== Skill Manifest ===\n")

    print(f"Agent: {MANIFEST.name} v{MANIFEST.version}")
    print(f"Protocols: {', '.join(MANIFEST.protocols)}")
    print(f"Categories: {', '.join(MANIFEST.categories)}")
    print()

    print("Skills by pricing tier:")
    for tier, skills in MANIFEST.pricing_summary().items():
        print(f"  {tier}: {', '.join(skills)}")
    print()

    print("Free skills (no API needed):")
    for s in MANIFEST.free_skills():
        print(f"  - {s.name}: {s.description[:60]}...")
    print()


def demo_a2a_card():
    """Show the A2A agent card for Google's Agent-to-Agent protocol."""
    import json
    card = MANIFEST.to_a2a_agent_card()
    print("=== A2A Agent Card ===\n")
    print(json.dumps(card, indent=2)[:500])
    print("  ...")
    print()


def demo_mcp_config():
    """Show the MCP config for Claude Desktop."""
    import json
    config = MANIFEST.to_mcp_manifest()
    print("=== Claude Desktop MCP Config ===\n")
    print("Add to claude_desktop_config.json:")
    print(json.dumps(config, indent=2))
    print()


if __name__ == "__main__":
    demo_mcp_tools()
    demo_tool_execution()
    demo_skill_manifest()
    demo_a2a_card()
    demo_mcp_config()
