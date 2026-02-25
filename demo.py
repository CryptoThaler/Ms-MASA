#!/usr/bin/env python3
"""
Ms-MASA Interactive Demo
========================
Walks through every capability layer of the Polymarket Agent Specialist.

Run:  python demo.py
"""

from __future__ import annotations

import json
import sys
import time
import textwrap

# ── Helpers ────────────────────────────────────────────────────────────

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def banner(text: str):
    w = 64
    print(f"\n{CYAN}{'═' * w}")
    print(f"  {BOLD}{text}{RESET}{CYAN}")
    print(f"{'═' * w}{RESET}\n")

def section(num: int, title: str):
    print(f"\n{YELLOW}── [{num}] {title} {'─' * (50 - len(title))}{RESET}\n")

def ok(msg: str):
    print(f"  {GREEN}✓{RESET} {msg}")

def info(msg: str):
    print(f"  {DIM}→ {msg}{RESET}")

def show_json(data, max_lines=15):
    text = json.dumps(data, indent=2, default=str)
    lines = text.split('\n')
    for line in lines[:max_lines]:
        print(f"    {DIM}{line}{RESET}")
    if len(lines) > max_lines:
        print(f"    {DIM}... ({len(lines) - max_lines} more lines){RESET}")

def show_text(text: str, max_lines=12):
    lines = text.strip().split('\n')
    for line in lines[:max_lines]:
        print(f"    {DIM}{line}{RESET}")
    if len(lines) > max_lines:
        print(f"    {DIM}... ({len(lines) - max_lines} more lines){RESET}")

def pause():
    print()


# ── Demo ───────────────────────────────────────────────────────────────

def main():
    banner("Ms-MASA: Polymarket Agent Specialist — Demo")

    print(f"  {BOLD}What is Ms-MASA?{RESET}")
    print(f"  A specialized AI agent toolkit for Polymarket prediction markets.")
    print(f"  Knowledge, live data, analysis, signals, and agent building —")
    print(f"  available via MCP, A2A, Fetch.ai, LangChain, and on-chain registries.")
    pause()

    # ── 1. Agent Status ────────────────────────────────────────────

    section(1, "Agent Initialization")
    from ms_masa.agent import MsMasaAgent
    agent = MsMasaAgent.from_env()
    status = agent.status()
    ok(f"Agent: {status['agent']} v{status['version']}")
    ok(f"Capabilities: {', '.join(status['capabilities'])}")
    ok(f"CLOB API: {'healthy' if status['clob_healthy'] else 'unavailable (sandbox)'}")
    ok(f"Auth: {'configured' if status['authenticated'] else 'read-only mode'}")
    pause()

    # ── 2. Knowledge Base ──────────────────────────────────────────

    section(2, "Knowledge Base (Zero API Calls)")

    from ms_masa.knowledge.polymarket_kb import PolymarketKB
    topics = PolymarketKB.topics()
    ok(f"Topics available: {len(topics)}")
    info(f"{', '.join(topics)}")
    pause()

    info("agent.explain('platform'):")
    platform = agent.explain("platform")
    show_json(platform)
    pause()

    info("agent.explain('apis'):")
    apis = agent.explain("apis")
    api_names = list(apis.keys()) if isinstance(apis, dict) else []
    ok(f"API sections: {', '.join(api_names)}")
    pause()

    info("agent.explain('orders'):")
    orders = agent.explain("orders")
    show_json(orders)
    pause()

    # ── 3. Reference Cards ─────────────────────────────────────────

    section(3, "Quick Reference Cards")

    cards = ["gamma_api", "clob_api", "order_flow", "auth_setup", "agent_architecture", "market_concepts"]
    ok(f"Available cards: {len(cards)}")
    info(f"{', '.join(cards)}")
    pause()

    info("agent.ref('gamma_api'):")
    show_text(agent.ref("gamma_api"))
    pause()

    info("agent.ref('agent_architecture'):")
    show_text(agent.ref("agent_architecture"))
    pause()

    # ── 4. Agent Context (Token-Optimized) ─────────────────────────

    section(4, "Agent Context Strings (Token-Optimized)")

    for agent_type in ["read_only_agent", "analytical_agent", "trading_agent"]:
        ctx = agent.get_agent_context(agent_type)
        ok(f"{agent_type}: {len(ctx)} chars")
    pause()

    info("agent.get_agent_context('read_only_agent') [first 500 chars]:")
    ctx = agent.get_agent_context("read_only_agent")
    show_text(ctx[:500])
    pause()

    # ── 5. Ecosystem Reference ─────────────────────────────────────

    section(5, "Ecosystem Reference")

    from ms_masa.knowledge.ecosystem import EcosystemReference as eco
    ok(f"Repos catalog: {len(eco.REPOS)} repositories")
    for name, repo in list(eco.REPOS.items())[:5]:
        purpose = repo["purpose"] if isinstance(repo, dict) else str(repo)[:60]
        info(f"  {name}: {purpose}")
    pause()

    info("Ecosystem summary:")
    show_text(eco.summary())
    pause()

    # ── 6. Agent Builder ───────────────────────────────────────────

    section(6, "Agent Builder (Code Generation)")

    from ms_masa.builder.agent_builder import AgentBuilder
    builder = AgentBuilder()
    from ms_masa.builder.templates import AgentTemplates
    templates = AgentTemplates.list_templates()
    ok(f"Templates available: {len(templates)}")
    for name, desc in templates.items():
        info(f"  {name}: {desc}")
    pause()

    info("builder.generate('market_monitor') [first 20 lines]:")
    code = builder.generate("market_monitor", write=False)
    show_text(code, max_lines=20)
    pause()

    # ── 7. Live Market Data (API) ──────────────────────────────────

    section(7, "Live Market Data (API)")

    info("Attempting API call to Polymarket Gamma...")
    try:
        markets = agent.scan_markets(limit=5, sort_by="volume")
        ok(f"Retrieved {len(markets)} markets")
        for m in markets[:3]:
            q = m.get("question", "?")[:50]
            p = m.get("yes_price", "?")
            v = m.get("volume", 0)
            info(f"  {q}... | Yes: {p} | Vol: {v:,.0f}")
    except Exception as e:
        info(f"API unavailable in this environment: {type(e).__name__}")
        info("(Markets data requires network access to gamma-api.polymarket.com)")
        ok("Knowledge-only mode works perfectly without API access")
    pause()

    # ── 8. MCP Server ─────────────────────────────────────────────

    section(8, "MCP Server (Model Context Protocol)")

    from ms_masa.mcp_server import TOOLS, RESOURCES
    ok(f"MCP Tools: {len(TOOLS)}")
    for t in TOOLS:
        info(f"  {t['name']}: {t['description'][:55]}...")
    pause()

    ok(f"MCP Resources: {len(RESOURCES)}")
    for r in RESOURCES:
        info(f"  {r['uri']}: {r['name']}")
    pause()

    info("Config for Claude Desktop / Claude Code:")
    show_json({"mcpServers": {"ms-masa": {"command": "python", "args": ["-m", "ms_masa.mcp_server"]}}})
    pause()

    # ── 9. A2A Server (Agent-to-Agent) ─────────────────────────────

    section(9, "A2A Server (Google Agent-to-Agent Protocol)")

    from ms_masa.a2a_server import AGENT_CARD, route_task
    ok(f"Agent Card: {AGENT_CARD['name']} v{AGENT_CARD['version']}")
    ok(f"A2A Skills: {len(AGENT_CARD['skills'])}")
    for s in AGENT_CARD["skills"]:
        info(f"  {s['id']}: {s['name']}")
    pause()

    info("Task routing demo:")
    test_msgs = [
        "How does Polymarket work?",
        "What are the CLOB endpoints?",
        "How does resolution work?",
        "Tell me about ecosystem repos",
        "Generate a market monitoring bot",
    ]
    for msg in test_msgs:
        result = route_task(msg)
        skill = result["skill"]
        extra = result.get("topic", result.get("template", ""))
        ok(f'  "{msg}" → skill={skill} {extra}')
    pause()

    info("Discovery URL: http://localhost:9999/.well-known/agent.json")
    info("Run: python -m ms_masa.a2a_server --port 9999")
    pause()

    # ── 10. Fetch.ai uAgent ────────────────────────────────────────

    section(10, "Fetch.ai uAgent (Agentverse)")

    from ms_masa.uagent_wrapper import MESSAGE_SCHEMAS
    ok(f"Message schemas: {len(MESSAGE_SCHEMAS)}")
    for name, schema in MESSAGE_SCHEMAS.items():
        info(f"  {name}: fields={list(schema.keys())}")
    pause()

    info("Run: python -m ms_masa.uagent_wrapper")
    info("Auto-registers on Almanac smart contract for discovery")
    pause()

    # ── 11. Framework Integrations ─────────────────────────────────

    section(11, "Framework Integrations")

    from ms_masa.integrations import (
        callable_tools,
        openai_function_definitions,
    )

    callables = callable_tools()
    ok(f"Framework-agnostic callables: {len(callables)}")
    for name in list(callables.keys())[:5]:
        info(f"  {name}()")

    oai = openai_function_definitions()
    ok(f"OpenAI function defs: {len(oai)}")
    for fn in oai[:3]:
        info(f"  {fn['name']}: {fn['description'][:50]}...")

    try:
        from ms_masa.integrations import langchain_tools
        lc = langchain_tools()
        ok(f"LangChain StructuredTools: {len(lc)}")
    except ImportError:
        info("LangChain: available (pip install langchain-core)")

    try:
        from ms_masa.integrations import crewai_tools
        crew = crewai_tools()
        ok(f"CrewAI tools: {len(crew)}")
    except ImportError:
        info("CrewAI: available (pip install crewai-tools)")

    try:
        from ms_masa.integrations import autogen_functions
        autogen = autogen_functions()
        ok(f"AutoGen callables: {len(autogen)}")
    except ImportError:
        info("AutoGen: available (pip install pyautogen)")
    pause()

    # ── 12. Skill Manifest & Marketplace ───────────────────────────

    section(12, "Skill Manifest & Marketplace")

    from ms_masa.skill_manifest import MANIFEST
    ok(f"Skills defined: {len(MANIFEST.skills)}")
    ok(f"Free skills: {len(MANIFEST.free_skills())} | API-backed: {len(MANIFEST.api_skills())}")
    pause()

    info("Pricing summary:")
    show_json(MANIFEST.pricing_summary())
    pause()

    info("Export formats:")
    ok("A2A Agent Card")
    show_json(MANIFEST.to_a2a_agent_card(), max_lines=6)
    pause()

    ok("MCP Manifest")
    show_json(MANIFEST.to_mcp_manifest(), max_lines=6)
    pause()

    ok("OLAS Registry")
    show_json(MANIFEST.to_olas_registry(), max_lines=6)
    pause()

    # ── 13. Skill NFTs ─────────────────────────────────────────────

    section(13, "Skill NFT Templates")

    from ms_masa.marketplace import SKILL_NFT_TEMPLATES
    ok(f"NFT templates: {len(SKILL_NFT_TEMPLATES)}")
    for name, nft in SKILL_NFT_TEMPLATES.items():
        meta = nft.to_erc721_metadata()
        info(f"  {meta['name']} ({meta['attributes'][0]['value']})")
        attrs = {a["trait_type"]: a["value"] for a in meta["attributes"]}
        info(f"    Skills: {attrs.get('skill_count', '?')} | Tier: {attrs.get('tier', '?')}")
    pause()

    # ── 14. Marketplace Adapter ────────────────────────────────────

    section(14, "Marketplace Adapter")

    from ms_masa.marketplace import MarketplaceAdapter
    adapter = MarketplaceAdapter()
    ad = adapter.advertise()
    ok(f"Advertise payload: {len(json.dumps(ad))} bytes")
    show_json(ad, max_lines=8)
    pause()

    # Simulate usage tracking
    adapter.record_usage("polymarket_explain", "demo-user")
    adapter.record_usage("polymarket_explain", "demo-user")
    adapter.record_usage("polymarket_scan_markets", "demo-user")
    billing = adapter.billing_summary("demo-user")
    ok(f"Usage tracking (demo-user):")
    show_json(billing)
    pause()

    # ── Summary ────────────────────────────────────────────────────

    banner("Demo Complete")

    print(f"  {BOLD}What you just saw:{RESET}")
    print(f"  {GREEN}✓{RESET} 15+ knowledge topics (zero API calls)")
    print(f"  {GREEN}✓{RESET} 6 reference cards for quick lookups")
    print(f"  {GREEN}✓{RESET} 3 agent context types (token-optimized)")
    print(f"  {GREEN}✓{RESET} 4 agent templates with code generation")
    print(f"  {GREEN}✓{RESET} 10 MCP tools + 4 resources")
    print(f"  {GREEN}✓{RESET} 7 A2A skills with NL task routing")
    print(f"  {GREEN}✓{RESET} 4 Fetch.ai message schemas")
    print(f"  {GREEN}✓{RESET} 5 framework integrations (LangChain, CrewAI, AutoGen, OpenAI, raw)")
    print(f"  {GREEN}✓{RESET} 9 skills with 4-tier pricing")
    print(f"  {GREEN}✓{RESET} 3 Skill NFT templates")
    print(f"  {GREEN}✓{RESET} Multi-protocol export (A2A, MCP, OLAS)")
    print(f"  {GREEN}✓{RESET} Usage tracking & metering")

    print(f"\n  {BOLD}6 Entry Points:{RESET}")
    print(f"  1. {CYAN}MCP Server{RESET}    → Claude Desktop / Claude Code / Cursor")
    print(f"  2. {CYAN}A2A Server{RESET}    → Any A2A-compatible agent")
    print(f"  3. {CYAN}Fetch.ai{RESET}      → Agentverse marketplace")
    print(f"  4. {CYAN}LangChain{RESET}     → LangChain / LangGraph apps")
    print(f"  5. {CYAN}On-Chain{RESET}      → OLAS / Skill NFTs / Morpheus")
    print(f"  6. {CYAN}Direct Import{RESET} → from ms_masa import MsMasaAgent")

    print(f"\n  {BOLD}Quick Start:{RESET}")
    print(f"  {DIM}python -m ms_masa status{RESET}              # Check agent status")
    print(f"  {DIM}python -m ms_masa explain platform{RESET}    # Knowledge lookup")
    print(f"  {DIM}python -m ms_masa ref all{RESET}             # All reference cards")
    print(f"  {DIM}python -m ms_masa build market_monitor{RESET}# Generate agent code")
    print(f"  {DIM}python -m ms_masa serve{RESET}               # Start MCP server")
    print(f"  {DIM}python -m ms_masa marketplace{RESET}         # Marketplace tools")
    print()


if __name__ == "__main__":
    main()
