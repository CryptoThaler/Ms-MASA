"""
Ms-MASA MCP Server - Expose Polymarket intelligence as MCP tools.

Model Context Protocol (MCP) is Anthropic's open standard for connecting
AI models to external data/tools. This module turns Ms-MASA into an MCP
server that any MCP-compatible client (Claude Desktop, Claude Code, Cursor,
Windsurf, custom agents) can discover and call.

Start the server:
    python -m ms_masa.mcp_server               # stdio transport (default)
    python -m ms_masa.mcp_server --sse 8080     # SSE transport on port

Protocol: https://modelcontextprotocol.io/specification
"""

from __future__ import annotations

import json
import sys
from typing import Any


# ── MCP Protocol Constants ─────────────────────────────────────────────

JSONRPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2024-11-05"

SERVER_INFO = {
    "name": "ms-masa",
    "version": "0.1.0",
}

CAPABILITIES = {
    "tools": {"listChanged": False},
    "resources": {"subscribe": False, "listChanged": False},
}

# ── Tool Definitions ───────────────────────────────────────────────────

TOOLS = [
    {
        "name": "polymarket_explain",
        "description": (
            "Look up Polymarket platform knowledge. Returns structured data "
            "about APIs, contracts, market structure, SDKs, order types, auth, "
            "and agent patterns. Use to understand how Polymarket works."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": (
                        "Knowledge topic: platform, apis, gamma, clob, orders, "
                        "auth, sdks, contracts, market_structure, patterns, "
                        "agent_patterns, websocket, fees, resolution, neg_risk"
                    ),
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "polymarket_reference",
        "description": (
            "Get a compact reference card for quick lookups. Cards cover API "
            "endpoints, order flow, auth setup, agent architecture, and market concepts."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "card": {
                    "type": "string",
                    "description": (
                        "Card name: gamma_api, clob_api, order_flow, auth_setup, "
                        "agent_architecture, market_concepts, all"
                    ),
                    "default": "all",
                },
            },
        },
    },
    {
        "name": "polymarket_agent_context",
        "description": (
            "Get a compact context string optimized for LLM consumption. "
            "Returns everything an LLM needs to know about building on Polymarket "
            "in minimal tokens. Use at the start of agent sessions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_type": {
                    "type": "string",
                    "description": "Agent type: read_only_agent, analytical_agent, trading_agent",
                    "default": "read_only_agent",
                },
            },
        },
    },
    {
        "name": "polymarket_scan_markets",
        "description": (
            "Scan live Polymarket prediction markets with filters. Returns "
            "compact summaries with prices, volume, liquidity, and certainty scores."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max markets to return", "default": 20},
                "tag": {"type": "string", "description": "Filter by category tag (e.g., politics, crypto, sports)"},
                "sort_by": {"type": "string", "description": "Sort: volume, liquidity, certainty, uncertainty", "default": "volume"},
                "min_volume": {"type": "number", "description": "Minimum volume filter", "default": 0},
                "min_liquidity": {"type": "number", "description": "Minimum liquidity filter", "default": 0},
            },
        },
    },
    {
        "name": "polymarket_search_markets",
        "description": "Search Polymarket markets by question text. Returns matching markets with prices and metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (e.g., 'election', 'bitcoin', 'AI')"},
                "limit": {"type": "integer", "description": "Max results", "default": 20},
            },
            "required": ["query"],
        },
    },
    {
        "name": "polymarket_analyze_market",
        "description": (
            "Deep analysis of a specific Polymarket market. Returns order book "
            "analysis, liquidity assessment, signals, and structural characteristics."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "market_id": {"type": "string", "description": "Polymarket market ID"},
            },
            "required": ["market_id"],
        },
    },
    {
        "name": "polymarket_order_book",
        "description": "Get and analyze an order book for a specific token. Returns spread, depth, imbalance, and concentration metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token_id": {"type": "string", "description": "CLOB token ID for the outcome"},
            },
            "required": ["token_id"],
        },
    },
    {
        "name": "polymarket_detect_signals",
        "description": (
            "Scan markets for analytical signals: wide spreads, order book "
            "imbalances, low liquidity, near-certainty, high uncertainty. "
            "Returns signals grouped by market."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Markets to scan", "default": 50},
                "spread_threshold": {"type": "number", "description": "Min spread to flag", "default": 0.05},
                "imbalance_threshold": {"type": "number", "description": "Min imbalance to flag", "default": 0.3},
            },
        },
    },
    {
        "name": "polymarket_ecosystem",
        "description": (
            "Get complete Polymarket developer ecosystem reference: all repos, "
            "contracts, WebSocket streams, fee formulas, resolution mechanics, "
            "and neg-risk multi-outcome architecture."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": (
                        "Section: repos, websocket, fees, resolution, neg_risk, "
                        "clob_endpoints, order_structure, subgraphs, agent_prompts, summary, all"
                    ),
                    "default": "summary",
                },
            },
        },
    },
    {
        "name": "polymarket_build_agent",
        "description": (
            "Generate ready-to-run Polymarket agent code from templates. "
            "Templates: market_monitor (price alerts), signal_scanner (signal detection), "
            "data_collector (snapshot collection), llm_analyst (LLM-powered analysis)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "template": {
                    "type": "string",
                    "description": "Template: market_monitor, signal_scanner, data_collector, llm_analyst",
                },
            },
            "required": ["template"],
        },
    },
]

# ── Resources (MCP Resources expose read-only data) ───────────────────

RESOURCES = [
    {
        "uri": "polymarket://knowledge/platform",
        "name": "Polymarket Platform Overview",
        "description": "Core platform knowledge: architecture, chains, tokens, and mechanics",
        "mimeType": "application/json",
    },
    {
        "uri": "polymarket://knowledge/apis",
        "name": "Polymarket API Reference",
        "description": "Complete Gamma and CLOB API endpoint reference",
        "mimeType": "application/json",
    },
    {
        "uri": "polymarket://knowledge/contracts",
        "name": "Polymarket Smart Contracts",
        "description": "Contract addresses, ABIs, and interaction patterns",
        "mimeType": "application/json",
    },
    {
        "uri": "polymarket://ecosystem/summary",
        "name": "Polymarket Ecosystem Summary",
        "description": "One-paragraph developer ecosystem summary",
        "mimeType": "text/plain",
    },
]


# ── Tool Execution ─────────────────────────────────────────────────────

def _get_agent():
    """Lazy-load the agent to avoid import overhead on tool listing."""
    from ms_masa.agent import MsMasaAgent
    return MsMasaAgent.from_env()


def _get_ecosystem():
    """Lazy-load ecosystem reference."""
    from ms_masa.knowledge.ecosystem import EcosystemReference
    return EcosystemReference


def execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Execute an MCP tool and return the result."""
    agent = _get_agent()

    if name == "polymarket_explain":
        return agent.explain(arguments["topic"])

    elif name == "polymarket_reference":
        card = arguments.get("card", "all")
        return agent.ref(card)

    elif name == "polymarket_agent_context":
        agent_type = arguments.get("agent_type", "read_only_agent")
        return agent.get_agent_context(agent_type)

    elif name == "polymarket_scan_markets":
        return agent.scan_markets(
            limit=arguments.get("limit", 20),
            tag=arguments.get("tag"),
            sort_by=arguments.get("sort_by", "volume"),
            min_volume=arguments.get("min_volume", 0),
            min_liquidity=arguments.get("min_liquidity", 0),
        )

    elif name == "polymarket_search_markets":
        return agent.search_markets(
            query=arguments["query"],
            limit=arguments.get("limit", 20),
        )

    elif name == "polymarket_analyze_market":
        return agent.analyze_market(arguments["market_id"])

    elif name == "polymarket_order_book":
        return agent.get_order_book(arguments["token_id"])

    elif name == "polymarket_detect_signals":
        return agent.detect_signals(
            limit=arguments.get("limit", 50),
            spread_threshold=arguments.get("spread_threshold", 0.05),
            imbalance_threshold=arguments.get("imbalance_threshold", 0.3),
        )

    elif name == "polymarket_ecosystem":
        eco = _get_ecosystem()
        section = arguments.get("section", "summary")
        if section == "summary":
            return eco.summary()
        elif section == "all":
            return {
                "repos": eco.REPOS,
                "websocket": eco.WEBSOCKET,
                "fees": eco.FEES,
                "resolution": eco.RESOLUTION,
                "neg_risk": eco.NEG_RISK,
                "order_structure": eco.ORDER_STRUCTURE,
                "subgraphs": eco.SUBGRAPHS,
            }
        else:
            return getattr(eco, section.upper(), f"Unknown section: {section}")

    elif name == "polymarket_build_agent":
        from ms_masa.builder.agent_builder import AgentBuilder
        builder = AgentBuilder()
        return builder.generate(arguments["template"], write=False)

    else:
        raise ValueError(f"Unknown tool: {name}")


def read_resource(uri: str) -> tuple[str, str]:
    """Read an MCP resource. Returns (content, mimeType)."""
    agent = _get_agent()

    if uri == "polymarket://knowledge/platform":
        data = agent.explain("platform")
        return json.dumps(data, indent=2, default=str), "application/json"

    elif uri == "polymarket://knowledge/apis":
        data = agent.explain("apis")
        return json.dumps(data, indent=2, default=str), "application/json"

    elif uri == "polymarket://knowledge/contracts":
        data = agent.explain("contracts")
        return json.dumps(data, indent=2, default=str), "application/json"

    elif uri == "polymarket://ecosystem/summary":
        eco = _get_ecosystem()
        return eco.summary(), "text/plain"

    else:
        raise ValueError(f"Unknown resource: {uri}")


# ── JSON-RPC Message Handling ──────────────────────────────────────────

def handle_message(msg: dict) -> dict | None:
    """Process a JSON-RPC message and return a response."""
    method = msg.get("method", "")
    msg_id = msg.get("id")
    params = msg.get("params", {})

    # Notifications (no id) don't need responses
    if msg_id is None and method == "notifications/initialized":
        return None

    if method == "initialize":
        return _result(msg_id, {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": CAPABILITIES,
            "serverInfo": SERVER_INFO,
        })

    elif method == "tools/list":
        return _result(msg_id, {"tools": TOOLS})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        try:
            result = execute_tool(tool_name, arguments)
            text = result if isinstance(result, str) else json.dumps(result, indent=2, default=str)
            return _result(msg_id, {
                "content": [{"type": "text", "text": text}],
                "isError": False,
            })
        except Exception as e:
            return _result(msg_id, {
                "content": [{"type": "text", "text": f"Error: {e}"}],
                "isError": True,
            })

    elif method == "resources/list":
        return _result(msg_id, {"resources": RESOURCES})

    elif method == "resources/read":
        uri = params.get("uri", "")
        try:
            content, mime = read_resource(uri)
            return _result(msg_id, {
                "contents": [{"uri": uri, "mimeType": mime, "text": content}],
            })
        except Exception as e:
            return _error(msg_id, -32602, str(e))

    elif method == "ping":
        return _result(msg_id, {})

    else:
        return _error(msg_id, -32601, f"Method not found: {method}")


def _result(msg_id: Any, result: Any) -> dict:
    return {"jsonrpc": JSONRPC_VERSION, "id": msg_id, "result": result}


def _error(msg_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": JSONRPC_VERSION, "id": msg_id, "error": {"code": code, "message": message}}


# ── Transport: stdio ───────────────────────────────────────────────────

def run_stdio():
    """Run MCP server over stdio (stdin/stdout JSON-RPC)."""
    import io

    # Use binary mode for Content-Length framing
    stdin = sys.stdin.buffer if hasattr(sys.stdin, "buffer") else sys.stdin
    stdout = sys.stdout.buffer if hasattr(sys.stdout, "buffer") else sys.stdout

    while True:
        try:
            # Read Content-Length header
            headers = {}
            while True:
                line = stdin.readline()
                if not line:
                    return  # EOF
                line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                line_str = line_str.strip()
                if not line_str:
                    break
                if ":" in line_str:
                    key, val = line_str.split(":", 1)
                    headers[key.strip().lower()] = val.strip()

            content_length = int(headers.get("content-length", 0))
            if content_length == 0:
                continue

            body = stdin.read(content_length)
            body_str = body.decode("utf-8") if isinstance(body, bytes) else body
            msg = json.loads(body_str)

            response = handle_message(msg)
            if response is not None:
                resp_bytes = json.dumps(response).encode("utf-8")
                header = f"Content-Length: {len(resp_bytes)}\r\n\r\n"
                header_bytes = header.encode("utf-8")
                if isinstance(stdout, io.RawIOBase) or hasattr(stdout, "write"):
                    stdout.write(header_bytes)
                    stdout.write(resp_bytes)
                    stdout.flush()

        except (json.JSONDecodeError, KeyError, ValueError):
            continue
        except (EOFError, BrokenPipeError):
            break


# ── Entry Point ────────────────────────────────────────────────────────

def main():
    """CLI entry point for the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Ms-MASA MCP Server")
    parser.add_argument(
        "--sse", type=int, metavar="PORT",
        help="Run with SSE transport on given port (default: stdio)",
    )
    parser.add_argument(
        "--list-tools", action="store_true",
        help="Print tool definitions and exit",
    )
    args = parser.parse_args()

    if args.list_tools:
        print(json.dumps(TOOLS, indent=2))
        return

    if args.sse:
        print(f"SSE transport on port {args.sse} (requires mcp[sse] package)", file=sys.stderr)
        print("For now, use stdio transport (default).", file=sys.stderr)
        sys.exit(1)

    run_stdio()


if __name__ == "__main__":
    main()
