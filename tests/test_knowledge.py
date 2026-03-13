"""Tests for ms_masa.knowledge.polymarket_kb."""

from ms_masa.knowledge.polymarket_kb import PolymarketKB


def test_topics_listing():
    topics = PolymarketKB.topics()
    assert isinstance(topics, list)
    assert "platform" in topics
    assert "apis" in topics
    assert "contracts" in topics
    assert len(topics) >= 10


def test_lookup_platform():
    result = PolymarketKB.lookup("platform")
    assert result is not None
    assert "name" in result
    assert result["name"] == "Polymarket"


def test_lookup_apis():
    result = PolymarketKB.lookup("apis")
    assert result is not None
    assert "gamma" in result
    assert "clob" in result


def test_lookup_gamma():
    result = PolymarketKB.lookup("gamma")
    assert result is not None
    assert "base" in result


def test_lookup_clob():
    result = PolymarketKB.lookup("clob")
    assert result is not None
    assert "public_endpoints" in result


def test_lookup_orders():
    result = PolymarketKB.lookup("orders")
    assert result is not None
    assert "GTC" in result
    assert "FOK" in result


def test_lookup_auth():
    result = PolymarketKB.lookup("auth")
    assert result is not None
    assert "signature_types" in result


def test_lookup_sdks():
    result = PolymarketKB.lookup("sdks")
    assert result is not None
    assert "py-clob-client" in result


def test_lookup_contracts():
    result = PolymarketKB.lookup("contracts")
    assert result is not None
    assert "ctf_exchange" in result


def test_lookup_market_structure():
    result = PolymarketKB.lookup("market_structure")
    assert result is not None
    assert "hierarchy" in result


def test_lookup_patterns():
    result = PolymarketKB.lookup("patterns")
    assert result is not None
    assert "read_only_agent" in result
    assert "analytical_agent" in result
    assert "trading_agent" in result


def test_lookup_unknown_topic():
    result = PolymarketKB.lookup("nonexistent_topic")
    assert result is None


def test_lookup_case_insensitive():
    result = PolymarketKB.lookup("PLATFORM")
    assert result is not None


def test_get_agent_context():
    ctx = PolymarketKB.get_agent_context("read_only_agent")
    assert isinstance(ctx, str)
    assert "POLYMARKET" in ctx
    assert "CLOB" in ctx


def test_get_agent_context_analytical():
    ctx = PolymarketKB.get_agent_context("analytical_agent")
    assert "LLM" in ctx or "analytical" in ctx.lower()


def test_get_agent_context_fallback():
    ctx = PolymarketKB.get_agent_context("nonexistent_agent")
    assert isinstance(ctx, str)
    assert len(ctx) > 0
