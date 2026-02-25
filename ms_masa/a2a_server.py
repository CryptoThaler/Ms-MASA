"""
Ms-MASA A2A Server - Google Agent-to-Agent protocol implementation.

A2A enables agent-to-agent communication via JSON-RPC over HTTP.
Other agents discover Ms-MASA at /.well-known/agent.json and send
tasks for Polymarket intelligence.

Install:
    pip install "a2a-sdk[all]"

Run:
    python -m ms_masa.a2a_server                    # port 9999
    python -m ms_masa.a2a_server --port 8080        # custom port

Discovery:
    curl http://localhost:9999/.well-known/agent.json

Protocol: https://a2a-protocol.org/latest/specification/
"""

from __future__ import annotations

import json
import sys
from typing import Any

# ── Agent Card (always available, no dependencies) ─────────────────────

AGENT_CARD = {
    "name": "Ms-MASA",
    "description": (
        "Polymarket prediction market intelligence agent. Expert knowledge base, "
        "live market data, order book analysis, signal detection, and agent builder "
        "toolkit for Polymarket prediction markets."
    ),
    "url": "http://localhost:9999/",
    "version": "0.1.0",
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
        "stateTransitionHistory": False,
    },
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain", "application/json"],
    "skills": [
        {
            "id": "ms-masa.explain",
            "name": "Polymarket Knowledge",
            "description": "Expert knowledge about Polymarket platform, APIs, contracts, SDKs, and agent patterns",
            "tags": ["polymarket", "knowledge", "prediction-markets", "defi"],
            "examples": [
                "How does Polymarket work?",
                "What are the CLOB API endpoints?",
                "Explain the order structure",
                "How does market resolution work?",
            ],
        },
        {
            "id": "ms-masa.scan_markets",
            "name": "Scan Markets",
            "description": "Scan live Polymarket prediction markets with volume, liquidity, and category filters",
            "tags": ["polymarket", "markets", "data", "prediction-markets"],
            "examples": [
                "Show me top crypto prediction markets",
                "Find high-volume political markets",
                "Scan markets sorted by uncertainty",
            ],
        },
        {
            "id": "ms-masa.analyze_market",
            "name": "Analyze Market",
            "description": "Deep analysis of a specific market: order book, liquidity, signals, structure",
            "tags": ["polymarket", "analysis", "orderbook", "signals"],
            "examples": [
                "Analyze the liquidity of market XYZ",
                "What signals does this market show?",
            ],
        },
        {
            "id": "ms-masa.detect_signals",
            "name": "Detect Signals",
            "description": "Scan for wide spreads, order book imbalances, low liquidity, near-certainty events",
            "tags": ["polymarket", "signals", "analysis", "trading"],
            "examples": [
                "Find markets with wide bid-ask spreads",
                "Detect order book imbalances",
                "Which markets are near certainty?",
            ],
        },
        {
            "id": "ms-masa.search_markets",
            "name": "Search Markets",
            "description": "Search Polymarket markets by question text",
            "tags": ["polymarket", "search", "markets"],
            "examples": [
                "Find markets about elections",
                "Search for AI regulation predictions",
            ],
        },
        {
            "id": "ms-masa.build_agent",
            "name": "Build Agent",
            "description": "Generate ready-to-run Polymarket agent code from templates",
            "tags": ["polymarket", "agent", "code-generation", "builder"],
            "examples": [
                "Generate a market monitoring bot",
                "Create a signal scanner agent",
            ],
        },
        {
            "id": "ms-masa.ecosystem",
            "name": "Ecosystem Reference",
            "description": "Complete Polymarket developer ecosystem: repos, contracts, WebSocket, fees, resolution",
            "tags": ["polymarket", "ecosystem", "developer", "reference"],
            "examples": [
                "What repos does Polymarket have?",
                "How do fees work?",
                "Explain the resolution process",
            ],
        },
    ],
}


# ── Task Router (maps natural language to Ms-MASA skills) ─────────────

def route_task(message: str) -> dict[str, Any]:
    """Route an incoming A2A task to the appropriate Ms-MASA skill."""
    from ms_masa.agent import MsMasaAgent
    agent = MsMasaAgent.from_env()

    msg = message.lower()

    # Knowledge queries
    knowledge_triggers = {
        "how does polymarket": "platform",
        "what is polymarket": "platform",
        "clob": "clob",
        "gamma": "gamma",
        "order": "orders",
        "auth": "auth",
        "sdk": "sdks",
        "contract": "contracts",
        "resolution": "resolution",
        "neg.risk": "neg_risk",
        "websocket": "websocket",
        "fee": "fees",
    }
    for trigger, topic in knowledge_triggers.items():
        if trigger in msg:
            result = agent.explain(topic)
            return {"skill": "explain", "topic": topic, "data": result}

    # Signal detection
    if any(w in msg for w in ["signal", "imbalance", "spread", "detect"]):
        result = agent.detect_signals(limit=30)
        return {"skill": "detect_signals", "data": result}

    # Market analysis (needs a market ID in the message)
    if "analyze" in msg or "analysis" in msg:
        # Try to extract a market ID (hex string or UUID-like)
        import re
        ids = re.findall(r'[0-9a-f]{8,}', msg)
        if ids:
            result = agent.analyze_market(ids[0])
            return {"skill": "analyze_market", "market_id": ids[0], "data": result}

    # Market search
    if any(w in msg for w in ["search", "find", "look for"]):
        # Extract the search query (everything after the trigger word)
        for w in ["search for", "find", "look for", "search"]:
            if w in msg:
                query = msg.split(w, 1)[1].strip().rstrip("?.")
                if query:
                    result = agent.search_markets(query, limit=10)
                    return {"skill": "search_markets", "query": query, "data": result}

    # Market scanning
    if any(w in msg for w in ["scan", "top", "show me", "list", "markets"]):
        tag = None
        for t in ["politics", "crypto", "sports", "science", "pop-culture"]:
            if t in msg:
                tag = t
                break
        sort_by = "uncertainty" if "uncertain" in msg else "volume"
        result = agent.scan_markets(limit=15, tag=tag, sort_by=sort_by)
        return {"skill": "scan_markets", "tag": tag, "sort_by": sort_by, "data": result}

    # Agent building
    if any(w in msg for w in ["build", "generate", "create", "template", "scaffold"]):
        template = "market_monitor"
        for t in ["signal_scanner", "data_collector", "llm_analyst"]:
            if t.replace("_", " ") in msg or t in msg:
                template = t
                break
        from ms_masa.builder.agent_builder import AgentBuilder
        builder = AgentBuilder()
        code = builder.generate(template, write=False)
        return {"skill": "build_agent", "template": template, "data": code}

    # Ecosystem reference
    if any(w in msg for w in ["ecosystem", "repo", "developer"]):
        from ms_masa.knowledge.ecosystem import EcosystemReference
        return {"skill": "ecosystem", "data": EcosystemReference.summary()}

    # Default: platform knowledge
    result = agent.explain("platform")
    return {"skill": "explain", "topic": "platform", "data": result}


# ── Minimal HTTP Server (stdlib, no dependencies) ─────────────────────

def run_http_server(port: int = 9999):
    """Run a minimal A2A-compatible HTTP server using only stdlib."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import uuid

    # In-memory task store
    tasks: dict[str, dict] = {}

    class A2AHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/.well-known/agent.json":
                card = AGENT_CARD.copy()
                card["url"] = f"http://localhost:{port}/"
                body = json.dumps(card, indent=2).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_error(404)

        def do_POST(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            try:
                msg = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return

            method = msg.get("method", "")
            msg_id = msg.get("id")
            params = msg.get("params", {})

            if method == "tasks/send":
                # Extract the user message
                message_parts = params.get("message", {}).get("parts", [])
                user_text = ""
                for part in message_parts:
                    if part.get("type") == "text":
                        user_text += part.get("text", "")

                if not user_text:
                    user_text = str(params.get("message", ""))

                # Execute the task
                try:
                    result = route_task(user_text)
                    data = result.get("data", result)
                    text_output = (
                        data if isinstance(data, str)
                        else json.dumps(data, indent=2, default=str)
                    )

                    task_id = params.get("id", str(uuid.uuid4()))
                    task = {
                        "id": task_id,
                        "status": {"state": "completed"},
                        "artifacts": [{
                            "parts": [{"type": "text", "text": text_output}],
                        }],
                    }
                    tasks[task_id] = task

                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": task,
                    }
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "id": params.get("id", str(uuid.uuid4())),
                            "status": {"state": "failed", "message": str(e)},
                        },
                    }

            elif method == "tasks/get":
                task_id = params.get("id", "")
                task = tasks.get(task_id)
                if task:
                    response = {"jsonrpc": "2.0", "id": msg_id, "result": task}
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32602, "message": f"Task not found: {task_id}"},
                    }

            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

            resp_body = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)

        def log_message(self, format, *args):
            # Suppress access logs for cleaner output
            pass

    server = HTTPServer(("0.0.0.0", port), A2AHandler)
    print(f"Ms-MASA A2A server running on http://localhost:{port}/", file=sys.stderr)
    print(f"Agent card: http://localhost:{port}/.well-known/agent.json", file=sys.stderr)
    print(f"Skills: {len(AGENT_CARD['skills'])}", file=sys.stderr)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", file=sys.stderr)
        server.server_close()


# ── Entry Point ────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Ms-MASA A2A Server")
    parser.add_argument("--port", type=int, default=9999, help="Port (default: 9999)")
    parser.add_argument("--card", action="store_true", help="Print agent card and exit")
    args = parser.parse_args()

    if args.card:
        card = AGENT_CARD.copy()
        card["url"] = f"http://localhost:{args.port}/"
        print(json.dumps(card, indent=2))
        return

    run_http_server(args.port)


if __name__ == "__main__":
    main()
