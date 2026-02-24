"""
Configuration management for Ms-MASA agent system.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PolymarketEndpoints:
    """Polymarket API endpoint configuration."""
    clob: str = "https://clob.polymarket.com"
    gamma: str = "https://gamma-api.polymarket.com"
    gamma_markets: str = "https://gamma-api.polymarket.com/markets"
    gamma_events: str = "https://gamma-api.polymarket.com/events"
    rpc: str = "https://polygon-rpc.com"
    chain_id: int = 137

    # Contract addresses (Polygon mainnet)
    exchange: str = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
    neg_risk_exchange: str = "0xC5d563A36AE78145C45a50134d48A1215220f80a"
    neg_risk_adapter: str = "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296"
    usdc: str = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    ctf: str = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"


@dataclass
class AgentConfig:
    """Agent behavior configuration."""
    max_context_tokens: int = 4096
    market_fetch_limit: int = 100
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    log_level: str = "INFO"
    market_categories: list[str] = field(default_factory=list)


@dataclass
class MsMasaConfig:
    """Root configuration for the Ms-MASA system."""
    endpoints: PolymarketEndpoints = field(default_factory=PolymarketEndpoints)
    agent: AgentConfig = field(default_factory=AgentConfig)

    # Auth - loaded from environment
    private_key: Optional[str] = None
    api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> MsMasaConfig:
        """Load configuration from environment variables."""
        config = cls()
        config.private_key = os.getenv("POLYGON_WALLET_PRIVATE_KEY")
        config.api_key = os.getenv("POLYMARKET_API_KEY")
        config.openai_api_key = os.getenv("OPENAI_API_KEY")

        custom_clob = os.getenv("POLYMARKET_CLOB_URL")
        if custom_clob:
            config.endpoints.clob = custom_clob

        custom_gamma = os.getenv("POLYMARKET_GAMMA_URL")
        if custom_gamma:
            config.endpoints.gamma = custom_gamma
            config.endpoints.gamma_markets = f"{custom_gamma}/markets"
            config.endpoints.gamma_events = f"{custom_gamma}/events"

        return config

    @classmethod
    def from_file(cls, path: str | Path) -> MsMasaConfig:
        """Load configuration from a JSON file, then overlay env vars."""
        config = cls.from_env()
        p = Path(path)
        if p.exists():
            with open(p) as f:
                data = json.load(f)

            if "endpoints" in data:
                for k, v in data["endpoints"].items():
                    if hasattr(config.endpoints, k):
                        setattr(config.endpoints, k, v)

            if "agent" in data:
                for k, v in data["agent"].items():
                    if hasattr(config.agent, k):
                        setattr(config.agent, k, v)
        return config

    @property
    def is_authenticated(self) -> bool:
        return self.private_key is not None

    @property
    def has_llm(self) -> bool:
        return self.openai_api_key is not None
