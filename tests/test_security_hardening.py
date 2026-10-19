"""Regression tests for network-server hardening."""

import json
import os
import socket
import stat
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from ms_masa import security
from ms_masa.a2a_server import MAX_BODY_BYTES, BoundedTaskStore, handle_jsonrpc, run_http_server
from ms_masa.marketplace import MarketplaceAdapter
from ms_masa.mcp_server import ecosystem_section, handle_message
from ms_masa.uagent_wrapper import resolve_seed

TOKEN = "t" * 32


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class SecurityHelperTests(unittest.TestCase):
    def test_loopback_detection(self):
        for host in ("127.0.0.1", "::1", "localhost"):
            self.assertTrue(security.is_loopback(host))
        for host in ("0.0.0.0", "10.0.0.5", "example.com"):
            self.assertFalse(security.is_loopback(host))

    def test_bind_policy_requires_token_off_loopback(self):
        security.enforce_bind_policy("127.0.0.1", None)
        security.enforce_bind_policy("0.0.0.0", TOKEN)
        with self.assertRaises(SystemExit):
            security.enforce_bind_policy("0.0.0.0", None)

    def test_short_token_rejected(self):
        with mock.patch.dict(os.environ, {security.AUTH_TOKEN_ENV: "short"}):
            with self.assertRaises(SystemExit):
                security.load_auth_token()

    def test_bearer_matching(self):
        self.assertTrue(security.bearer_matches(None, None))
        self.assertTrue(security.bearer_matches(f"Bearer {TOKEN}", TOKEN))
        self.assertFalse(security.bearer_matches(None, TOKEN))
        self.assertFalse(security.bearer_matches("Bearer wrong", TOKEN))
        self.assertFalse(security.bearer_matches(TOKEN, TOKEN))

    def test_public_error_hides_details(self):
        with self.assertLogs("ms_masa.security", level="ERROR"):
            msg = security.public_error(RuntimeError("/secret/path leaked"))
        self.assertNotIn("/secret/path", msg)
        self.assertIn("RuntimeError", msg)


class A2AHandlerTests(unittest.TestCase):
    def test_task_store_is_bounded(self):
        store = BoundedTaskStore(max_tasks=3)
        for i in range(10):
            store.put(str(i), {"id": str(i)})
        self.assertEqual(len(store), 3)
        self.assertIsNone(store.get("0"))
        self.assertIsNotNone(store.get("9"))

    def test_failed_task_does_not_leak_exception(self):
        with mock.patch("ms_masa.a2a_server.route_task", side_effect=RuntimeError("/etc/private")), \
                self.assertLogs("ms_masa.security", level="ERROR"):
            resp = handle_jsonrpc(
                {"method": "tasks/send", "id": 1,
                 "params": {"message": {"parts": [{"type": "text", "text": "hi"}]}}},
                BoundedTaskStore(),
            )
        self.assertEqual(resp["result"]["status"]["state"], "failed")
        self.assertNotIn("/etc/private", json.dumps(resp))

    def test_rejects_malformed_requests(self):
        store = BoundedTaskStore()
        self.assertIn("error", handle_jsonrpc([], store))
        self.assertIn("error", handle_jsonrpc({"method": "tasks/send", "params": "x"}, store))
        self.assertIn("error", handle_jsonrpc({"method": "tasks/get", "params": {"id": "x" * 500}}, store))
        self.assertIn("error", handle_jsonrpc({"method": "tasks/send", "params": {"message": {}}}, store))


class A2AServerTests(unittest.TestCase):
    """Runs the real HTTP server with a token on loopback."""

    @classmethod
    def setUpClass(cls):
        cls.port = _free_port()
        cls.env = mock.patch.dict(os.environ, {security.AUTH_TOKEN_ENV: TOKEN})
        cls.env.start()
        threading.Thread(target=run_http_server, args=(cls.port, "127.0.0.1"), daemon=True).start()
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", cls.port), timeout=0.1).close()
                break
            except OSError:
                time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()

    def _post(self, body: bytes, token: str | None = TOKEN, headers: dict | None = None):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/", data=body, method="POST")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, None

    def test_agent_card_is_public_and_advertises_bearer(self):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/.well-known/agent.json", timeout=5) as r:
            card = json.loads(r.read())
        self.assertEqual(card["authentication"]["schemes"], ["bearer"])

    def test_post_requires_token(self):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tasks/get", "params": {"id": "x"}}).encode()
        self.assertEqual(self._post(body, token=None)[0], 401)
        self.assertEqual(self._post(body, token="wrong-token-wrong-token")[0], 401)
        self.assertEqual(self._post(body)[0], 200)

    def test_oversized_body_rejected_without_reading(self):
        sock = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        sock.sendall(
            f"POST / HTTP/1.1\r\nHost: x\r\nAuthorization: Bearer {TOKEN}\r\n"
            f"Content-Length: {MAX_BODY_BYTES + 1}\r\n\r\n".encode()
        )
        status_line = sock.recv(64).decode()
        sock.close()
        self.assertIn("413", status_line)

    def test_task_roundtrip(self):
        send = {"jsonrpc": "2.0", "id": 1, "method": "tasks/send",
                "params": {"id": "t1", "message": {"parts": [{"type": "text", "text": "How does Polymarket work?"}]}}}
        status, resp = self._post(json.dumps(send).encode())
        self.assertEqual(status, 200)
        self.assertEqual(resp["result"]["status"]["state"], "completed")
        status, resp = self._post(json.dumps({"id": 2, "method": "tasks/get", "params": {"id": "t1"}}).encode())
        self.assertEqual(resp["result"]["id"], "t1")


class McpServerTests(unittest.TestCase):
    def test_ecosystem_rejects_unknown_sections(self):
        for section in ("__class__", "__dict__", "summary_x", "mro"):
            self.assertIn("error", ecosystem_section(section))
        self.assertIsInstance(ecosystem_section("summary"), str)

    def test_tool_errors_are_opaque(self):
        with mock.patch("ms_masa.mcp_server.execute_tool", side_effect=RuntimeError("/home/secret")), \
                self.assertLogs("ms_masa.security", level="ERROR"):
            resp = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                   "params": {"name": "polymarket_explain", "arguments": {}}})
        self.assertTrue(resp["result"]["isError"])
        self.assertNotIn("/home/secret", json.dumps(resp))


class McpV2Tests(unittest.TestCase):
    def setUp(self):
        try:
            import mcp.server.fastmcp  # noqa: F401
        except ImportError:
            self.skipTest("mcp<2 not installed")

    def test_http_app_requires_bearer_when_token_set(self):
        from starlette.testclient import TestClient
        from ms_masa.mcp_server_v2 import build_http_app

        app = build_http_app("streamable-http", "127.0.0.1", 8000, TOKEN)
        with TestClient(app, base_url="http://127.0.0.1:8000") as client:
            self.assertEqual(client.post("/mcp", json={}).status_code, 401)
            ok = client.post(
                "/mcp",
                headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json, text/event-stream"},
                json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                    "protocolVersion": "2025-03-26", "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0"}}},
            )
            self.assertEqual(ok.status_code, 200)


class UAgentSeedTests(unittest.TestCase):
    def test_generated_seed_is_random_persisted_and_private(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MS_MASA_UAGENT_SEED", None)
            path = Path(d) / "sub" / "seed"
            first = resolve_seed(seed_path=path)
            self.assertEqual(first, resolve_seed(seed_path=path))
            self.assertGreaterEqual(len(first), 64)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            other = resolve_seed(seed_path=Path(d) / "other")
            self.assertNotEqual(first, other)

    def test_short_explicit_seed_rejected(self):
        with self.assertRaises(SystemExit):
            resolve_seed("ms-masa-polymarket-agent")


class MarketplaceTests(unittest.TestCase):
    def test_usage_log_bounded_but_billing_exact(self):
        adapter = MarketplaceAdapter(max_usage_records=5)
        for _ in range(20):
            adapter.record_usage("explain", "alice")
        adapter.record_usage("scan_markets", "bob", success=False)
        self.assertEqual(len(adapter.usage_log), 5)
        self.assertEqual(adapter.billing_summary("alice")["total_calls"], 20)
        self.assertEqual(adapter.billing_summary()["failed"], 1)
        self.assertEqual(adapter.billing_summary()["total_calls"], 21)


if __name__ == "__main__":
    unittest.main()


class McpStdioCompatibilityTests(unittest.TestCase):
    """Both servers must speak the MCP stdio transport that real clients use."""

    def _list_tools_with_sdk_client(self, module: str) -> list[str]:
        import asyncio
        import sys
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def run():
            params = StdioServerParameters(command=sys.executable, args=["-m", module])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    result = await session.call_tool("polymarket_explain", {"topic": "fees"})
                    self.assertFalse(result.isError)
                    return [t.name for t in tools.tools]

        return asyncio.run(asyncio.wait_for(run(), timeout=60))

    def setUp(self):
        try:
            import mcp.client.stdio  # noqa: F401
        except ImportError:
            self.skipTest("mcp<2 not installed")

    def test_fastmcp_server_works_with_sdk_client(self):
        names = self._list_tools_with_sdk_client("ms_masa.mcp_server_v2")
        self.assertIn("polymarket_scan_markets", names)

    def test_fallback_server_works_with_sdk_client(self):
        names = self._list_tools_with_sdk_client("ms_masa.mcp_server")
        self.assertEqual(len(names), 10)

    def test_fallback_stdio_framing(self):
        import io
        from ms_masa.mcp_server import MAX_MESSAGE_BYTES, run_stdio
        lines = [
            b"{not json\n",
            b"x" * (MAX_MESSAGE_BYTES + 10) + b"\n",
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode() + b"\n",
            json.dumps({"jsonrpc": "2.0", "id": 7, "method": "ping"}).encode() + b"\n",
        ]
        out = io.BytesIO()
        with self.assertLogs("ms_masa.mcp", level="WARNING"):
            run_stdio(io.BytesIO(b"".join(lines)), out)
        replies = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual([r.get("error", {}).get("code") for r in replies], [-32700, -32600, None])
        self.assertEqual(replies[2]["id"], 7)
