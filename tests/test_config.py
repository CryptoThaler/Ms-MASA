"""Tests for ms_masa.config configuration management."""

import json
import os
import tempfile

from ms_masa.config import AgentConfig, MsMasaConfig, PolymarketEndpoints


def test_default_endpoints():
    ep = PolymarketEndpoints()
    assert ep.clob == "https://clob.polymarket.com"
    assert ep.gamma == "https://gamma-api.polymarket.com"
    assert ep.chain_id == 137


def test_default_agent_config():
    ac = AgentConfig()
    assert ac.max_context_tokens == 4096
    assert ac.enable_caching is True


def test_config_defaults():
    cfg = MsMasaConfig()
    assert cfg.private_key is None
    assert cfg.is_authenticated is False
    assert cfg.has_llm is False


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("POLYGON_WALLET_PRIVATE_KEY", "0xtest123")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test456")
    monkeypatch.setenv("POLYMARKET_CLOB_URL", "https://custom-clob.example.com")
    monkeypatch.setenv("POLYMARKET_GAMMA_URL", "https://custom-gamma.example.com")

    cfg = MsMasaConfig.from_env()
    assert cfg.private_key == "0xtest123"
    assert cfg.is_authenticated is True
    assert cfg.has_llm is True
    assert cfg.endpoints.clob == "https://custom-clob.example.com"
    assert cfg.endpoints.gamma == "https://custom-gamma.example.com"
    assert cfg.endpoints.gamma_markets == "https://custom-gamma.example.com/markets"


def test_config_from_file():
    config_data = {
        "endpoints": {"chain_id": 80001},
        "agent": {"max_context_tokens": 8192, "log_level": "DEBUG"},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        path = f.name

    try:
        cfg = MsMasaConfig.from_file(path)
        assert cfg.endpoints.chain_id == 80001
        assert cfg.agent.max_context_tokens == 8192
        assert cfg.agent.log_level == "DEBUG"
    finally:
        os.unlink(path)


def test_config_from_nonexistent_file():
    cfg = MsMasaConfig.from_file("/nonexistent/path.json")
    # Should still return a valid config with defaults
    assert cfg.endpoints.clob == "https://clob.polymarket.com"
