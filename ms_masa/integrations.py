"""
Ms-MASA Integrations - Plug into LangChain, CrewAI, AutoGen, and more.

Provides ready-to-use tool wrappers for popular agent frameworks.
Each integration converts Ms-MASA skills into the framework's native
tool format so they work seamlessly in existing agent pipelines.

Usage:
    # LangChain
    from ms_masa.integrations import langchain_tools
    tools = langchain_tools()

    # CrewAI
    from ms_masa.integrations import crewai_tools
    tools = crewai_tools()

    # AutoGen
    from ms_masa.integrations import autogen_functions

    # Generic (any framework)
    from ms_masa.integrations import callable_tools
    tools = callable_tools()
"""

from __future__ import annotations

import json
from typing import Callable

from ms_masa.agent import MsMasaAgent
from ms_masa.skill_manifest import MANIFEST


# ── Shared Agent Instance ──────────────────────────────────────────────

_agent: MsMasaAgent | None = None


def _get_agent() -> MsMasaAgent:
    """Get or create a shared agent instance."""
    global _agent
    if _agent is None:
        _agent = MsMasaAgent.from_env()
    return _agent


# ── Generic Callable Tools ─────────────────────────────────────────────

def callable_tools() -> dict[str, Callable]:
    """
    Return Ms-MASA skills as plain callables.

    Works with any framework that accepts Python functions as tools.
    Each function accepts **kwargs matching the skill's input schema.
    """
    agent = _get_agent()

    def explain(topic: str = "platform") -> str:
        """Look up Polymarket platform knowledge."""
        result = agent.explain(topic)
        return json.dumps(result, indent=2, default=str)

    def reference_card(card: str = "all") -> str:
        """Get a compact Polymarket reference card."""
        return agent.ref(card)

    def agent_context(agent_type: str = "read_only_agent") -> str:
        """Get compact LLM context for Polymarket agent building."""
        return agent.get_agent_context(agent_type)

    def scan_markets(
        limit: int = 20,
        tag: str | None = None,
        sort_by: str = "volume",
        min_volume: float = 0,
        min_liquidity: float = 0,
    ) -> str:
        """Scan live Polymarket prediction markets."""
        result = agent.scan_markets(
            limit=limit, tag=tag, sort_by=sort_by,
            min_volume=min_volume, min_liquidity=min_liquidity,
        )
        return json.dumps(result, indent=2, default=str)

    def search_markets(query: str, limit: int = 20) -> str:
        """Search Polymarket markets by question text."""
        result = agent.search_markets(query, limit=limit)
        return json.dumps(result, indent=2, default=str)

    def analyze_market(market_id: str) -> str:
        """Deep analysis of a specific Polymarket market."""
        result = agent.analyze_market(market_id)
        return json.dumps(result, indent=2, default=str)

    def order_book(token_id: str) -> str:
        """Get and analyze an order book."""
        result = agent.get_order_book(token_id)
        return json.dumps(result, indent=2, default=str)

    def detect_signals(
        limit: int = 50,
        spread_threshold: float = 0.05,
        imbalance_threshold: float = 0.3,
    ) -> str:
        """Scan markets for analytical signals."""
        result = agent.detect_signals(
            limit=limit,
            spread_threshold=spread_threshold,
            imbalance_threshold=imbalance_threshold,
        )
        return json.dumps(result, indent=2, default=str)

    def build_agent(template: str) -> str:
        """Generate Polymarket agent code from template."""
        from ms_masa.builder.agent_builder import AgentBuilder
        builder = AgentBuilder()
        return builder.generate(template, write=False)

    def ecosystem(section: str = "summary") -> str:
        """Get Polymarket developer ecosystem reference."""
        from ms_masa.knowledge.ecosystem import EcosystemReference as eco
        if section == "summary":
            return eco.summary()
        return json.dumps(getattr(eco, section.upper(), {}), indent=2, default=str)

    return {
        "polymarket_explain": explain,
        "polymarket_reference_card": reference_card,
        "polymarket_agent_context": agent_context,
        "polymarket_scan_markets": scan_markets,
        "polymarket_search_markets": search_markets,
        "polymarket_analyze_market": analyze_market,
        "polymarket_order_book": order_book,
        "polymarket_detect_signals": detect_signals,
        "polymarket_build_agent": build_agent,
        "polymarket_ecosystem_reference": ecosystem,
    }


# ── LangChain Integration ─────────────────────────────────────────────

def langchain_tools() -> list:
    """
    Create LangChain Tool objects for all Ms-MASA skills.

    Usage:
        from ms_masa.integrations import langchain_tools
        from langchain.agents import create_react_agent

        tools = langchain_tools()
        agent = create_react_agent(llm, tools, prompt)
    """
    try:
        from langchain_core.tools import StructuredTool
    except ImportError:
        raise ImportError(
            "langchain-core is required for LangChain integration. "
            "Install with: pip install langchain-core"
        )

    tools_map = callable_tools()
    lc_tools = []

    for skill in MANIFEST.skills:
        func = tools_map.get(f"polymarket_{skill.name}")
        if func is None:
            continue

        tool = StructuredTool.from_function(
            func=func,
            name=f"polymarket_{skill.name}",
            description=skill.description,
        )
        lc_tools.append(tool)

    return lc_tools


# ── CrewAI Integration ─────────────────────────────────────────────────

def crewai_tools() -> list:
    """
    Create CrewAI Tool objects for all Ms-MASA skills.

    Usage:
        from ms_masa.integrations import crewai_tools
        from crewai import Agent

        polymarket_analyst = Agent(
            role="Polymarket Analyst",
            tools=crewai_tools(),
            goal="Analyze prediction market opportunities",
        )
    """
    try:
        from crewai.tools import tool as crewai_tool
    except ImportError:
        raise ImportError(
            "crewai is required for CrewAI integration. "
            "Install with: pip install crewai"
        )

    tools_map = callable_tools()
    crew_tools = []

    for skill in MANIFEST.skills:
        func = tools_map.get(f"polymarket_{skill.name}")
        if func is None:
            continue
        # CrewAI uses decorated functions as tools
        decorated = crewai_tool(func)
        crew_tools.append(decorated)

    return crew_tools


# ── AutoGen Integration ────────────────────────────────────────────────

def autogen_functions() -> dict[str, Callable]:
    """
    Return functions suitable for AutoGen function calling.

    Usage:
        from ms_masa.integrations import autogen_functions

        functions = autogen_functions()
        for name, func in functions.items():
            assistant.register_for_llm(
                description=func.__doc__
            )(func)
    """
    return callable_tools()


# ── OpenAI Function Calling ────────────────────────────────────────────

def openai_function_definitions() -> list[dict]:
    """
    Generate OpenAI-compatible function definitions.

    Use with the OpenAI API's function calling feature or
    any compatible provider (Together, Groq, etc).

    Usage:
        from ms_masa.integrations import openai_function_definitions
        functions = openai_function_definitions()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=[{"type": "function", "function": f} for f in functions],
        )
    """
    definitions = []
    for skill in MANIFEST.skills:
        properties = {}
        required = []
        for param_name, param_def in skill.input_schema.items():
            prop = {
                "type": param_def.get("type", "string"),
                "description": param_def.get("description", ""),
            }
            if "default" in param_def:
                prop["default"] = param_def["default"]
            properties[param_name] = prop
            if param_def.get("required"):
                required.append(param_name)

        definitions.append({
            "name": f"polymarket_{skill.name}",
            "description": skill.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        })

    return definitions


def execute_openai_function(name: str, arguments: dict) -> str:
    """Execute a function call from OpenAI's response."""
    tools = callable_tools()
    func = tools.get(name)
    if func is None:
        return json.dumps({"error": f"Unknown function: {name}"})
    try:
        return func(**arguments)
    except Exception as e:
        return json.dumps({"error": str(e)})
