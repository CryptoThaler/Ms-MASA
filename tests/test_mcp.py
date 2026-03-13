"""Tests for ms_masa.mcp_server message handling."""

from ms_masa.mcp_server import (
    CAPABILITIES,
    MCP_PROTOCOL_VERSION,
    SERVER_INFO,
    TOOLS,
    handle_message,
)


def test_initialize():
    msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    resp = handle_message(msg)
    assert resp["id"] == 1
    assert resp["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION
    assert resp["result"]["serverInfo"] == SERVER_INFO
    assert "tools" in resp["result"]["capabilities"]


def test_tools_list():
    msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    resp = handle_message(msg)
    assert resp["id"] == 2
    tools = resp["result"]["tools"]
    assert len(tools) >= 9
    names = [t["name"] for t in tools]
    assert "polymarket_explain" in names
    assert "polymarket_scan_markets" in names
    assert "polymarket_detect_signals" in names


def test_resources_list():
    msg = {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}}
    resp = handle_message(msg)
    assert resp["id"] == 3
    resources = resp["result"]["resources"]
    assert len(resources) >= 3


def test_ping():
    msg = {"jsonrpc": "2.0", "id": 4, "method": "ping", "params": {}}
    resp = handle_message(msg)
    assert resp["id"] == 4
    assert "result" in resp


def test_unknown_method():
    msg = {"jsonrpc": "2.0", "id": 5, "method": "nonexistent/method", "params": {}}
    resp = handle_message(msg)
    assert "error" in resp
    assert resp["error"]["code"] == -32601


def test_notification_no_response():
    msg = {"method": "notifications/initialized", "params": {}}
    resp = handle_message(msg)
    assert resp is None


def test_tool_definitions_have_schemas():
    for tool in TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"


def test_tools_call_explain():
    msg = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {"name": "polymarket_explain", "arguments": {"topic": "platform"}},
    }
    resp = handle_message(msg)
    assert resp["id"] == 6
    assert resp["result"]["isError"] is False
    assert len(resp["result"]["content"]) > 0


def test_tools_call_unknown():
    msg = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {"name": "nonexistent_tool", "arguments": {}},
    }
    resp = handle_message(msg)
    assert resp["result"]["isError"] is True
