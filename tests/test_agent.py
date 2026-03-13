"""Tests for ms_masa.agent core agent."""

import json

from ms_masa.agent import MsMasaAgent
from ms_masa.config import MsMasaConfig


def test_agent_instantiation():
    agent = MsMasaAgent()
    assert agent.profile.name == "Ms-MASA"
    assert agent.profile.version == "0.1.0"


def test_agent_capabilities():
    agent = MsMasaAgent()
    cap_names = [c.name for c in agent.profile.capabilities]
    assert "knowledge" in cap_names
    assert "market_data" in cap_names
    assert "analysis" in cap_names
    assert "signals" in cap_names
    assert "builder" in cap_names


def test_explain_platform():
    agent = MsMasaAgent()
    result = agent.explain("platform")
    assert result is not None
    assert "name" in result
    assert result["name"] == "Polymarket"


def test_explain_all_topics():
    agent = MsMasaAgent()
    from ms_masa.knowledge.polymarket_kb import PolymarketKB
    for topic in PolymarketKB.topics():
        result = agent.explain(topic)
        assert result is not None, f"explain('{topic}') returned None"


def test_explain_unknown():
    agent = MsMasaAgent()
    result = agent.explain("nonexistent")
    assert "error" in result
    assert "available" in result


def test_ref_all():
    agent = MsMasaAgent()
    result = agent.ref("all")
    assert isinstance(result, str)
    assert len(result) > 100


def test_ref_specific_cards():
    agent = MsMasaAgent()
    for card in ["gamma_api", "clob_api", "order_flow", "auth_setup",
                 "agent_architecture", "market_concepts"]:
        result = agent.ref(card)
        assert isinstance(result, str), f"ref('{card}') did not return str"
        assert len(result) > 20, f"ref('{card}') too short"


def test_get_agent_context():
    agent = MsMasaAgent()
    ctx = agent.get_agent_context("read_only_agent")
    assert isinstance(ctx, str)
    assert "POLYMARKET" in ctx


def test_status():
    agent = MsMasaAgent()
    status = agent.status()
    assert status["agent"] == "Ms-MASA"
    assert "clob_healthy" in status
    assert "capabilities" in status


def test_compact_json():
    data = {"key": "value", "num": 42}
    result = MsMasaAgent.compact_json(data)
    assert isinstance(result, str)
    # Compact JSON should have no spaces
    parsed = json.loads(result)
    assert parsed == data


def test_agent_from_config():
    cfg = MsMasaConfig()
    agent = MsMasaAgent(config=cfg)
    assert agent.config is cfg
