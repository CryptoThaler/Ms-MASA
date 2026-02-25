"""
Ms-MASA Skill Manifest - Agent-to-Agent skill advertisement.

Defines Ms-MASA's capabilities as tradeable/discoverable skills in agentic
ecosystems. Compatible with multiple marketplace patterns:

1. MCP Discovery   - Tools discoverable via MCP protocol
2. A2A Protocol    - Google Agent-to-Agent agent cards
3. OLAS Registry   - Autonolas on-chain service registration
4. Direct Import   - Python import for LangChain/CrewAI/AutoGen

Each skill has: name, description, input/output schema, pricing tier,
and authentication requirements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── Pricing Tiers ──────────────────────────────────────────────────────

class PricingTier(str, Enum):
    FREE = "free"               # No auth, knowledge lookups
    METERED = "metered"         # Per-call pricing for API-backed queries
    SUBSCRIPTION = "subscription"  # Flat rate for unlimited access
    PREMIUM = "premium"         # Trading capabilities, requires auth


# ── Skill Definition ───────────────────────────────────────────────────

@dataclass
class SkillDefinition:
    """A single skill that Ms-MASA can perform."""
    name: str
    description: str
    category: str              # knowledge, market_data, analysis, signals, builder
    pricing: PricingTier
    requires_auth: bool = False
    requires_api: bool = False  # Needs live Polymarket API access
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)
    examples: list[dict] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_mcp_tool(self) -> dict:
        """Convert to MCP tool definition."""
        return {
            "name": f"polymarket_{self.name}",
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.input_schema,
                "required": [k for k, v in self.input_schema.items() if v.get("required")],
            },
        }

    def to_a2a_skill(self) -> dict:
        """Convert to Google A2A protocol skill format."""
        return {
            "id": f"ms-masa.{self.name}",
            "name": self.name.replace("_", " ").title(),
            "description": self.description,
            "tags": self.tags,
            "examples": [ex.get("prompt", "") for ex in self.examples],
        }

    def to_langchain_tool(self) -> dict:
        """Convert to LangChain tool spec."""
        return {
            "name": f"polymarket_{self.name}",
            "description": self.description,
            "args_schema": self.input_schema,
        }

    def to_olas_service(self) -> dict:
        """Convert to Autonolas (OLAS) service component descriptor."""
        return {
            "name": f"ms_masa_{self.name}",
            "description": self.description,
            "version": "0.1.0",
            "author": "ms-masa",
            "type": "skill",
            "protocols": [],
            "behaviours": {
                self.name: {
                    "class_name": f"MsMasa{self.name.title().replace('_', '')}Behaviour",
                    "args": {},
                },
            },
        }


# ── Skill Registry ────────────────────────────────────────────────────

SKILLS: list[SkillDefinition] = [
    SkillDefinition(
        name="explain",
        description="Look up Polymarket platform knowledge. Covers APIs, contracts, market structure, SDKs, order types, auth, and agent patterns.",
        category="knowledge",
        pricing=PricingTier.FREE,
        input_schema={
            "topic": {
                "type": "string",
                "description": "Topic: platform, apis, gamma, clob, orders, auth, sdks, contracts, market_structure, patterns",
                "required": True,
            },
        },
        output_schema={"type": "object", "description": "Structured knowledge data"},
        examples=[
            {"prompt": "How does Polymarket work?", "args": {"topic": "platform"}},
            {"prompt": "What are the CLOB API endpoints?", "args": {"topic": "clob"}},
        ],
        tags=["polymarket", "knowledge", "prediction-markets", "defi"],
    ),
    SkillDefinition(
        name="reference_card",
        description="Get a compact reference card for Polymarket APIs, order flow, auth, or architecture.",
        category="knowledge",
        pricing=PricingTier.FREE,
        input_schema={
            "card": {
                "type": "string",
                "description": "Card: gamma_api, clob_api, order_flow, auth_setup, agent_architecture, market_concepts, all",
                "default": "all",
            },
        },
        output_schema={"type": "string", "description": "Formatted reference card"},
        examples=[{"prompt": "Show me the CLOB API reference", "args": {"card": "clob_api"}}],
        tags=["polymarket", "reference", "api"],
    ),
    SkillDefinition(
        name="agent_context",
        description="Get compact LLM context string for Polymarket agent building. Minimal tokens, maximum information.",
        category="knowledge",
        pricing=PricingTier.FREE,
        input_schema={
            "agent_type": {
                "type": "string",
                "description": "Agent type: read_only_agent, analytical_agent, trading_agent",
                "default": "read_only_agent",
            },
        },
        output_schema={"type": "string", "description": "Compact context for LLM consumption"},
        examples=[{"prompt": "I need context to build a Polymarket bot", "args": {"agent_type": "analytical_agent"}}],
        tags=["polymarket", "agent", "llm", "context"],
    ),
    SkillDefinition(
        name="scan_markets",
        description="Scan live Polymarket prediction markets with filters. Returns prices, volume, liquidity, certainty.",
        category="market_data",
        pricing=PricingTier.METERED,
        requires_api=True,
        input_schema={
            "limit": {"type": "integer", "default": 20},
            "tag": {"type": "string", "description": "Category filter"},
            "sort_by": {"type": "string", "default": "volume"},
            "min_volume": {"type": "number", "default": 0},
        },
        output_schema={"type": "array", "items": {"type": "object"}, "description": "Market summaries"},
        examples=[{"prompt": "Show me top crypto prediction markets", "args": {"tag": "crypto", "limit": 10}}],
        tags=["polymarket", "markets", "data", "prediction-markets"],
    ),
    SkillDefinition(
        name="search_markets",
        description="Search Polymarket markets by question text.",
        category="market_data",
        pricing=PricingTier.METERED,
        requires_api=True,
        input_schema={
            "query": {"type": "string", "description": "Search text", "required": True},
            "limit": {"type": "integer", "default": 20},
        },
        output_schema={"type": "array", "items": {"type": "object"}},
        examples=[{"prompt": "Find markets about the 2026 elections", "args": {"query": "election 2026"}}],
        tags=["polymarket", "search", "markets"],
    ),
    SkillDefinition(
        name="analyze_market",
        description="Deep analysis of a specific market: order book, liquidity, signals, structure.",
        category="analysis",
        pricing=PricingTier.METERED,
        requires_api=True,
        input_schema={
            "market_id": {"type": "string", "description": "Polymarket market ID", "required": True},
        },
        output_schema={"type": "object", "description": "Deep market analysis"},
        examples=[{"prompt": "Analyze this market's liquidity and signals", "args": {"market_id": "0x..."}}],
        tags=["polymarket", "analysis", "orderbook", "signals"],
    ),
    SkillDefinition(
        name="detect_signals",
        description="Scan markets for analytical signals: wide spreads, imbalances, low liquidity, near-certainty.",
        category="signals",
        pricing=PricingTier.METERED,
        requires_api=True,
        input_schema={
            "limit": {"type": "integer", "default": 50},
            "spread_threshold": {"type": "number", "default": 0.05},
            "imbalance_threshold": {"type": "number", "default": 0.3},
        },
        output_schema={"type": "object", "description": "Signals grouped by market ID"},
        examples=[{"prompt": "Find prediction markets with wide bid-ask spreads", "args": {"spread_threshold": 0.08}}],
        tags=["polymarket", "signals", "trading", "analysis"],
    ),
    SkillDefinition(
        name="build_agent",
        description="Generate ready-to-run Polymarket agent code from templates.",
        category="builder",
        pricing=PricingTier.FREE,
        input_schema={
            "template": {
                "type": "string",
                "description": "Template: market_monitor, signal_scanner, data_collector, llm_analyst",
                "required": True,
            },
        },
        output_schema={"type": "string", "description": "Complete Python agent code"},
        examples=[{"prompt": "Generate a market monitoring bot", "args": {"template": "market_monitor"}}],
        tags=["polymarket", "agent", "code-generation", "builder"],
    ),
    SkillDefinition(
        name="ecosystem_reference",
        description="Complete Polymarket developer ecosystem: repos, contracts, WebSocket, fees, resolution, neg-risk.",
        category="knowledge",
        pricing=PricingTier.FREE,
        input_schema={
            "section": {
                "type": "string",
                "description": "Section: repos, websocket, fees, resolution, neg_risk, clob_endpoints, order_structure, summary, all",
                "default": "summary",
            },
        },
        output_schema={"type": "object", "description": "Ecosystem reference data"},
        tags=["polymarket", "ecosystem", "developer", "reference"],
    ),
]


# ── Manifest (the top-level advertisement) ─────────────────────────────

@dataclass
class AgentManifest:
    """
    Ms-MASA's complete skill manifest for agentic marketplaces.

    This is what gets advertised to other agents, registries, and
    marketplace protocols.
    """
    name: str = "Ms-MASA"
    version: str = "0.1.0"
    description: str = (
        "Polymarket Agent Specialist. Expert knowledge base, live market data, "
        "analysis engine, signal detection, and agent builder toolkit for "
        "Polymarket prediction markets."
    )
    author: str = "ms-masa"
    license: str = "MIT"
    homepage: str = "https://github.com/CryptoThaler/Ms-MASA"

    # Capability categories
    categories: list[str] = field(default_factory=lambda: [
        "prediction-markets",
        "defi",
        "market-data",
        "agent-building",
        "knowledge-base",
    ])

    # Protocol support
    protocols: list[str] = field(default_factory=lambda: [
        "mcp",           # Anthropic Model Context Protocol
        "a2a",           # Google Agent-to-Agent
        "langchain",     # LangChain tool interface
        "direct-python", # Direct Python import
    ])

    skills: list[SkillDefinition] = field(default_factory=lambda: SKILLS)

    def to_a2a_agent_card(self) -> dict:
        """
        Generate a Google A2A Agent Card.

        A2A is Google's open protocol for agent-to-agent communication.
        Agent Cards are JSON documents that describe an agent's capabilities.
        Spec: https://google.github.io/A2A/
        """
        return {
            "name": self.name,
            "description": self.description,
            "url": self.homepage,
            "version": self.version,
            "capabilities": {
                "streaming": False,
                "pushNotifications": False,
            },
            "authentication": {
                "schemes": ["none"],  # Free tier needs no auth
            },
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "skills": [s.to_a2a_skill() for s in self.skills],
        }

    def to_mcp_manifest(self) -> dict:
        """Generate MCP server manifest for Claude Desktop / Claude Code."""
        return {
            "mcpServers": {
                "ms-masa": {
                    "command": "python",
                    "args": ["-m", "ms_masa.mcp_server"],
                    "env": {},
                },
            },
        }

    def to_olas_registry(self) -> dict:
        """
        Generate Autonolas (OLAS) service registration descriptor.

        OLAS is an on-chain protocol for autonomous agent services.
        Services are registered on Ethereum/Gnosis Chain and composed
        from reusable components.
        """
        return {
            "name": f"ms_masa_polymarket_service",
            "description": self.description,
            "version": self.version,
            "license": self.license,
            "components": [s.to_olas_service() for s in self.skills],
            "connections": [],
            "protocols": ["polymarket_gamma_v1", "polymarket_clob_v1"],
            "dependencies": {
                "skills": {f"ms_masa/{s.name}:0.1.0": {} for s in self.skills},
            },
        }

    def to_langchain_toolkit(self) -> list[dict]:
        """Generate LangChain-compatible tool definitions."""
        return [s.to_langchain_tool() for s in self.skills]

    def pricing_summary(self) -> dict:
        """Summarize pricing across all skills."""
        tiers: dict[str, list[str]] = {}
        for s in self.skills:
            tier = s.pricing.value
            tiers.setdefault(tier, []).append(s.name)
        return tiers

    def free_skills(self) -> list[SkillDefinition]:
        """Skills that require no API access (pure knowledge)."""
        return [s for s in self.skills if s.pricing == PricingTier.FREE]

    def api_skills(self) -> list[SkillDefinition]:
        """Skills that require live Polymarket API access."""
        return [s for s in self.skills if s.requires_api]


# ── Convenience ────────────────────────────────────────────────────────

MANIFEST = AgentManifest()


def get_manifest() -> AgentManifest:
    """Get the global skill manifest."""
    return MANIFEST
