"""
Ms-MASA MCP Server v2 - FastMCP Implementation.

Upgraded from raw JSON-RPC to the official MCP Python SDK (FastMCP).
Supports stdio, SSE, and streamable HTTP transports out of the box.

Install:
    pip install "mcp[cli]<2"

Run:
    python -m ms_masa.mcp_server_v2                        # stdio (Claude Desktop/Code)
    python -m ms_masa.mcp_server_v2 --http 8080            # HTTP on 127.0.0.1
    python -m ms_masa.mcp_server_v2 --sse 8080             # SSE on 127.0.0.1
    MS_MASA_AUTH_TOKEN=... python -m ms_masa.mcp_server_v2 --http 8080 --host 0.0.0.0
                                                           # remote: bearer token required

Test with MCP Inspector:
    npx @modelcontextprotocol/inspector python -m ms_masa.mcp_server_v2

Claude Desktop config:
    {"mcpServers": {"ms-masa": {"command": "python", "args": ["-m", "ms_masa.mcp_server_v2"]}}}
"""

from __future__ import annotations

import json
import sys
from typing import Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "FastMCP requires the MCP SDK v1: pip install 'mcp[cli]<2'\n"
        "Falling back to ms_masa.mcp_server (raw JSON-RPC).",
        file=sys.stderr,
    )
    from ms_masa.mcp_server import main
    main()
    sys.exit(0)


# ── Server Setup ───────────────────────────────────────────────────────

mcp = FastMCP(
    "ms-masa",
    instructions=(
        "Polymarket Agent Specialist - knowledge, live market data, "
        "analysis, signals, and agent builder for prediction markets."
    ),
)

# Lazy agent singleton
_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        from ms_masa.agent import MsMasaAgent
        _agent = MsMasaAgent.from_env()
    return _agent


# ── Tools ──────────────────────────────────────────────────────────────

@mcp.tool()
def polymarket_explain(topic: str) -> str:
    """Look up Polymarket platform knowledge.

    Topics: platform, apis, gamma, clob, orders, auth, sdks,
    contracts, market_structure, patterns, agent_patterns,
    websocket, fees, resolution, neg_risk
    """
    result = _get_agent().explain(topic)
    if result is None:
        from ms_masa.knowledge.polymarket_kb import PolymarketKB
        return json.dumps({"error": f"Unknown topic: {topic}", "available": PolymarketKB.topics()})
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def polymarket_reference(card: str = "all") -> str:
    """Get a compact reference card for Polymarket.

    Cards: gamma_api, clob_api, order_flow, auth_setup,
    agent_architecture, market_concepts, all
    """
    return _get_agent().ref(card)


@mcp.tool()
def polymarket_agent_context(agent_type: str = "read_only_agent") -> str:
    """Get a compact LLM context string for Polymarket agent building.

    Minimal tokens, maximum information. Use at the start of agent sessions.
    Agent types: read_only_agent, analytical_agent, trading_agent
    """
    return _get_agent().get_agent_context(agent_type)


@mcp.tool()
def polymarket_scan_markets(
    limit: int = 20,
    tag: Optional[str] = None,
    sort_by: str = "volume",
    min_volume: float = 0,
    min_liquidity: float = 0,
) -> str:
    """Scan live Polymarket prediction markets with filters.

    Returns compact summaries with prices, volume, liquidity,
    and certainty scores. Sort by: volume, liquidity, certainty, uncertainty.
    Tags: politics, crypto, sports, science, pop-culture, etc.
    """
    result = _get_agent().scan_markets(
        limit=limit, tag=tag, sort_by=sort_by,
        min_volume=min_volume, min_liquidity=min_liquidity,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def polymarket_search_markets(query: str, limit: int = 20) -> str:
    """Search Polymarket markets by question text.

    Returns matching markets with prices and metadata.
    Example queries: 'election', 'bitcoin', 'AI regulation', 'World Cup'
    """
    result = _get_agent().search_markets(query, limit=limit)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def polymarket_analyze_market(market_id: str) -> str:
    """Deep analysis of a specific Polymarket market.

    Returns order book analysis, liquidity assessment, analytical
    signals, and structural characteristics.
    """
    result = _get_agent().analyze_market(market_id)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def polymarket_order_book(token_id: str) -> str:
    """Get and analyze an order book for a specific outcome token.

    Returns spread, depth, imbalance, and concentration metrics.
    Use clob_token_ids from market data to get token IDs.
    """
    result = _get_agent().get_order_book(token_id)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def polymarket_detect_signals(
    limit: int = 50,
    spread_threshold: float = 0.05,
    imbalance_threshold: float = 0.3,
) -> str:
    """Scan markets for analytical signals.

    Detects: wide spreads, order book imbalances, low liquidity,
    near-certainty events, and high-uncertainty markets.
    Returns signals grouped by market ID.
    """
    result = _get_agent().detect_signals(
        limit=limit,
        spread_threshold=spread_threshold,
        imbalance_threshold=imbalance_threshold,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def polymarket_ecosystem(section: str = "summary") -> str:
    """Get Polymarket developer ecosystem reference.

    Sections: repos, websocket, fees, resolution, neg_risk,
    clob_endpoints, order_structure, subgraphs, agent_prompts, summary, all
    """
    from ms_masa.mcp_server import ecosystem_section
    data = ecosystem_section(section)
    return data if isinstance(data, str) else json.dumps(data, indent=2, default=str)


@mcp.tool()
def polymarket_build_agent(template: str) -> str:
    """Generate ready-to-run Polymarket agent code from templates.

    Templates: market_monitor (price alerts), signal_scanner (signal detection),
    data_collector (snapshot collection), llm_analyst (LLM-powered analysis).
    Returns complete, runnable Python code.
    """
    from ms_masa.builder.agent_builder import AgentBuilder
    builder = AgentBuilder()
    return builder.generate(template, write=False)


# ── Resources ──────────────────────────────────────────────────────────

@mcp.resource("polymarket://knowledge/{topic}")
def knowledge_resource(topic: str) -> str:
    """Polymarket knowledge base - structured platform data."""
    result = _get_agent().explain(topic)
    return json.dumps(result, indent=2, default=str) if result else f"Unknown topic: {topic}"


@mcp.resource("polymarket://ecosystem/summary")
def ecosystem_summary() -> str:
    """One-paragraph Polymarket developer ecosystem summary."""
    from ms_masa.knowledge.ecosystem import EcosystemReference
    return EcosystemReference.summary()


@mcp.resource("polymarket://reference/{card}")
def reference_resource(card: str) -> str:
    """Quick reference cards for Polymarket APIs and concepts."""
    return _get_agent().ref(card)


@mcp.resource("polymarket://context/{agent_type}")
def context_resource(agent_type: str) -> str:
    """Compact LLM context strings for different agent types."""
    return _get_agent().get_agent_context(agent_type)


# ── Entry Point ────────────────────────────────────────────────────────

def build_http_app(transport: str, host: str, port: int, token: str | None):
    """Build the ASGI app for a network transport, wrapped in bearer auth if a token is set."""
    from ms_masa.security import BearerAuthASGI, is_loopback

    mcp.settings.host = host
    mcp.settings.port = port
    if not is_loopback(host):
        # The SDK's DNS-rebinding guard only allows loopback Host headers by default;
        # remote deployments are protected by the bearer token instead.
        from mcp.server.transport_security import TransportSecuritySettings
        mcp.settings.transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

    app = mcp.streamable_http_app() if transport == "streamable-http" else mcp.sse_app()
    return BearerAuthASGI(app, token) if token else app


def main():
    """CLI entry point for the FastMCP server."""
    import argparse
    from ms_masa.security import AUTH_TOKEN_ENV, DEFAULT_HOST, enforce_bind_policy, load_auth_token

    parser = argparse.ArgumentParser(
        description="Ms-MASA MCP Server v2 (FastMCP)",
        epilog=f"Binding a non-loopback host requires {AUTH_TOKEN_ENV} to be set.",
    )
    parser.add_argument("--http", type=int, metavar="PORT", help="Run with streamable HTTP on port")
    parser.add_argument("--sse", type=int, metavar="PORT", help="Run with SSE transport on port")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Bind address for HTTP/SSE (default: {DEFAULT_HOST})")
    parser.add_argument("--list-tools", action="store_true", help="List tools and exit")
    args = parser.parse_args()

    if args.list_tools:
        for t in mcp._tool_manager.list_tools():
            print(f"  {t.name}: {(t.description or '').strip().splitlines()[0][:60]}")
        return

    if not (args.http or args.sse):
        mcp.run()  # stdio default
        return

    import uvicorn

    token = load_auth_token()
    enforce_bind_policy(args.host, token)
    transport = "streamable-http" if args.http else "sse"
    port = args.http or args.sse
    app = build_http_app(transport, args.host, port, token)
    print(f"Ms-MASA MCP ({transport}) on http://{args.host}:{port}/ "
          f"(auth: {'bearer token' if token else 'none, loopback only'})", file=sys.stderr)
    uvicorn.run(app, host=args.host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
