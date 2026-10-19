"""
Ms-MASA A2A Server - Google Agent-to-Agent protocol implementation.

A2A enables agent-to-agent communication via JSON-RPC over HTTP.
Other agents discover Ms-MASA at /.well-known/agent.json and send
tasks for Polymarket intelligence.

Install:
    pip install "a2a-sdk[all]"

Run:
    python -m ms_masa.a2a_server                    # 127.0.0.1:9999, no auth
    python -m ms_masa.a2a_server --port 8080        # custom port
    MS_MASA_AUTH_TOKEN=... python -m ms_masa.a2a_server --host 0.0.0.0
                                                    # remote: bearer token required

Discovery:
    curl http://localhost:9999/.well-known/agent.json

Protocol: https://a2a-protocol.org/latest/specification/
"""

from __future__ import annotations

import json
import os
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

MAX_BODY_BYTES = 1_048_576
MAX_TASKS = 1000
MAX_TASK_ID_LENGTH = 128
REQUEST_TIMEOUT_SECONDS = 30


class BoundedTaskStore:
    """FIFO-evicting task store so memory stays bounded under load."""

    def __init__(self, max_tasks: int = MAX_TASKS):
        from collections import OrderedDict
        import threading
        self._tasks: OrderedDict[str, dict] = OrderedDict()
        self._max = max_tasks
        self._lock = threading.Lock()

    def put(self, task_id: str, task: dict) -> None:
        with self._lock:
            self._tasks.pop(task_id, None)
            self._tasks[task_id] = task
            while len(self._tasks) > self._max:
                self._tasks.popitem(last=False)

    def get(self, task_id: str) -> dict | None:
        with self._lock:
            return self._tasks.get(task_id)

    def __len__(self) -> int:
        return len(self._tasks)


def build_agent_card(host: str, port: int, auth_required: bool) -> dict:
    card = dict(AGENT_CARD)
    display_host = "localhost" if host in ("127.0.0.1", "::1") else host
    card["url"] = f"http://{display_host}:{port}/"
    card["authentication"] = {"schemes": ["bearer"] if auth_required else ["none"]}
    return card


def _jsonrpc_error(msg_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle_jsonrpc(msg: Any, tasks: BoundedTaskStore) -> dict:
    """Dispatch one A2A JSON-RPC request. Never exposes internal error text."""
    import uuid
    from ms_masa.security import public_error

    if not isinstance(msg, dict):
        return _jsonrpc_error(None, -32600, "Invalid request")

    method = msg.get("method", "")
    msg_id = msg.get("id")
    params = msg.get("params") or {}
    if not isinstance(params, dict):
        return _jsonrpc_error(msg_id, -32602, "params must be an object")

    task_id = params.get("id")
    if task_id is not None and (not isinstance(task_id, str) or len(task_id) > MAX_TASK_ID_LENGTH):
        return _jsonrpc_error(msg_id, -32602, f"id must be a string of at most {MAX_TASK_ID_LENGTH} chars")

    if method == "tasks/send":
        task_id = task_id or str(uuid.uuid4())
        message = params.get("message")
        parts = message.get("parts", []) if isinstance(message, dict) else []
        user_text = "".join(
            p.get("text", "") for p in parts
            if isinstance(p, dict) and p.get("type") == "text" and isinstance(p.get("text"), str)
        )
        if not user_text:
            return _jsonrpc_error(msg_id, -32602, "message.parts must contain a text part")

        try:
            result = route_task(user_text)
            data = result.get("data", result)
            text_output = data if isinstance(data, str) else json.dumps(data, indent=2, default=str)
            task = {
                "id": task_id,
                "status": {"state": "completed"},
                "artifacts": [{"parts": [{"type": "text", "text": text_output}]}],
            }
        except Exception as e:
            task = {
                "id": task_id,
                "status": {"state": "failed", "message": public_error(e, "a2a task")},
            }
        tasks.put(task_id, task)
        return {"jsonrpc": "2.0", "id": msg_id, "result": task}

    if method == "tasks/get":
        task = tasks.get(task_id or "")
        if task:
            return {"jsonrpc": "2.0", "id": msg_id, "result": task}
        return _jsonrpc_error(msg_id, -32602, "Task not found")

    return _jsonrpc_error(msg_id, -32601, "Method not found")


def run_http_server(port: int = 9999, host: str | None = None):
    """Run a minimal A2A-compatible HTTP server using only stdlib."""
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    from ms_masa.security import DEFAULT_HOST, bearer_matches, enforce_bind_policy, load_auth_token

    host = host or DEFAULT_HOST
    token = load_auth_token()
    enforce_bind_policy(host, token)

    tasks = BoundedTaskStore()
    card_body = json.dumps(build_agent_card(host, port, token is not None), indent=2).encode()

    class A2AHandler(BaseHTTPRequestHandler):
        timeout = REQUEST_TIMEOUT_SECONDS

        def _send_json(self, status: int, payload: bytes, extra_headers: dict | None = None):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            for k, v in (extra_headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            # Agent card stays public so other agents can discover auth requirements.
            if self.path == "/.well-known/agent.json":
                self._send_json(200, card_body)
            else:
                self._send_json(404, b'{"error":"not found"}')

        def do_POST(self):
            if not bearer_matches(self.headers.get("Authorization"), token):
                self._send_json(401, b'{"error":"unauthorized"}', {"WWW-Authenticate": "Bearer"})
                return

            try:
                content_length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self._send_json(411, b'{"error":"Content-Length required"}')
                return
            if content_length < 0 or content_length > MAX_BODY_BYTES:
                self.close_connection = True
                self._send_json(413, b'{"error":"request body too large"}')
                return

            try:
                msg = json.loads(self.rfile.read(content_length))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send_json(200, json.dumps(_jsonrpc_error(None, -32700, "Parse error")).encode())
                return

            response = handle_jsonrpc(msg, tasks)
            self._send_json(200, json.dumps(response).encode())

        def log_message(self, format, *args):
            pass

    ThreadingHTTPServer.daemon_threads = True
    server = ThreadingHTTPServer((host, port), A2AHandler)
    print(f"Ms-MASA A2A server on http://{host}:{port}/ "
          f"(auth: {'bearer token' if token else 'none, loopback only'})", file=sys.stderr)
    print(f"Agent card: http://{host}:{port}/.well-known/agent.json", file=sys.stderr)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", file=sys.stderr)
    finally:
        server.server_close()


# ── Entry Point ────────────────────────────────────────────────────────

def main():
    import argparse
    import logging
    from ms_masa.security import AUTH_TOKEN_ENV, DEFAULT_HOST

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    parser = argparse.ArgumentParser(
        description="Ms-MASA A2A Server",
        epilog=f"Binding a non-loopback host requires {AUTH_TOKEN_ENV} to be set.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Bind address (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=9999, help="Port (default: 9999)")
    parser.add_argument("--card", action="store_true", help="Print agent card and exit")
    args = parser.parse_args()

    if args.card:
        print(json.dumps(build_agent_card(args.host, args.port, bool(os.getenv(AUTH_TOKEN_ENV))), indent=2))
        return

    run_http_server(args.port, args.host)


if __name__ == "__main__":
    main()
