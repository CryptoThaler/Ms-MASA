"""
Ms-MASA Core Agent - Polymarket Specialist.

The central agent class that orchestrates all modules:
- Knowledge base for instant Polymarket reference
- API clients for live market data
- Analysis engine for market intelligence
- Signal detection for opportunity identification
- Builder interface for creating specialized sub-agents

Designed for LOW TOKEN USE: compact outputs, structured data,
minimal prompt overhead.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from ms_masa.api.gamma import GammaClient
from ms_masa.api.clob import ClobClient
from ms_masa.api.data_pipe import DataPipeline
from ms_masa.analysis.market_analyzer import MarketAnalyzer
from ms_masa.analysis.signals import SignalEngine
from ms_masa.config import MsMasaConfig
from ms_masa.knowledge.polymarket_kb import PolymarketKB
from ms_masa.knowledge.reference import QuickReference
from ms_masa.models import (
    AgentCapability,
    AgentProfile,
    Event,
    Market,
    MarketSignal,
    MarketSnapshot,
)

logger = logging.getLogger(__name__)


class MsMasaAgent:
    """
    Ms-MASA: Polymarket Agent Specialist.

    A low-token, high-performance agent for understanding and building
    on the Polymarket prediction market platform.

    Usage:
        agent = MsMasaAgent()                    # Read-only mode
        agent = MsMasaAgent.from_env()           # With env credentials
        agent = MsMasaAgent.from_config("cfg.json")  # From config file

    Core capabilities:
        agent.explain(topic)       -> Platform knowledge lookup
        agent.ref(card)            -> Quick reference card
        agent.scan_markets(...)    -> Live market scanning
        agent.analyze_market(id)   -> Deep market analysis
        agent.detect_signals(...)  -> Signal detection
        agent.build_agent(spec)    -> Generate agent code
    """

    def __init__(self, config: Optional[MsMasaConfig] = None):
        self.config = config or MsMasaConfig()
        self.kb = PolymarketKB
        self.ref_cards = QuickReference
        self.analyzer = MarketAnalyzer()
        self.signals = SignalEngine()
        self.pipeline = DataPipeline(self.config)
        self.gamma = self.pipeline.gamma
        self.clob = self.pipeline.clob

        self.profile = AgentProfile(
            name="Ms-MASA",
            version="0.1.0",
            capabilities=[
                AgentCapability("knowledge", "Polymarket platform knowledge", "knowledge"),
                AgentCapability("market_data", "Live market data access", "api"),
                AgentCapability("analysis", "Market structure analysis", "analysis"),
                AgentCapability("signals", "Signal detection", "analysis"),
                AgentCapability("builder", "Agent builder toolkit", "builder"),
            ],
        )

    @classmethod
    def from_env(cls) -> MsMasaAgent:
        """Create agent with configuration from environment variables."""
        return cls(MsMasaConfig.from_env())

    @classmethod
    def from_config(cls, path: str) -> MsMasaAgent:
        """Create agent from a configuration file."""
        return cls(MsMasaConfig.from_file(path))

    # ── Knowledge Interface ────────────────────────────────────────────

    def explain(self, topic: str) -> Any:
        """Look up a topic in the Polymarket knowledge base.

        Topics: platform, apis, gamma, clob, orders, auth, sdks,
                contracts, market_structure, patterns
        """
        result = self.kb.lookup(topic)
        if result is None:
            return {
                "error": f"Unknown topic: {topic}",
                "available": self.kb.topics(),
            }
        return result

    def ref(self, card: str = "all") -> str:
        """Get a quick reference card.

        Cards: gamma_api, clob_api, order_flow, auth_setup,
               agent_architecture, market_concepts, all
        """
        card_map = {
            "gamma_api": self.ref_cards.gamma_api,
            "clob_api": self.ref_cards.clob_api,
            "order_flow": self.ref_cards.order_flow,
            "auth_setup": self.ref_cards.auth_setup,
            "agent_architecture": self.ref_cards.agent_architecture,
            "market_concepts": self.ref_cards.market_concepts,
            "all": self.ref_cards.all_references,
        }
        fn = card_map.get(card, self.ref_cards.all_references)
        return fn()

    def get_agent_context(self, agent_type: str = "read_only_agent") -> str:
        """Get a compact context string for LLM consumption."""
        return self.kb.get_agent_context(agent_type)

    # ── Live Market Data ───────────────────────────────────────────────

    def scan_markets(
        self,
        limit: int = 50,
        tag: Optional[str] = None,
        min_volume: float = 0,
        min_liquidity: float = 0,
        sort_by: str = "volume",
    ) -> list[dict]:
        """Scan live markets with filters, returning compact summaries."""
        if tag:
            markets = self.pipeline.scan_markets_by_tag(tag, limit=limit * 2)
        else:
            markets = self.gamma.get_tradeable_markets(limit=limit * 2)

        markets = self.analyzer.filter_markets(
            markets, min_volume=min_volume, min_liquidity=min_liquidity
        )
        markets = self.analyzer.rank_markets(markets, by=sort_by)[:limit]

        return [self.analyzer.characterize_market(m) for m in markets]

    def search_markets(self, query: str, limit: int = 20) -> list[dict]:
        """Search markets by question text."""
        markets = self.pipeline.search_markets(query, limit=limit)
        return [self.analyzer.characterize_market(m) for m in markets]

    def analyze_market(self, market_id: str) -> dict:
        """Deep analysis of a specific market."""
        raw = self.gamma.get_market(market_id)
        market = GammaClient._parse_market(raw)
        snapshot = self.pipeline.get_market_snapshot(market)
        analysis = self.analyzer.analyze_snapshot(snapshot)
        signals = self.signals.generate_signals(snapshot)
        analysis["signals"] = [
            {"type": s.signal_type, "strength": s.strength, "desc": s.description}
            for s in signals
        ]
        return analysis

    def get_order_book(self, token_id: str) -> dict:
        """Get and analyze an order book."""
        book = self.clob.get_order_book(token_id)
        return self.analyzer.analyze_order_book(book)

    def get_event(self, event_id: str) -> dict:
        """Get and analyze an event with all its markets."""
        raw = self.gamma.get_event(event_id)
        event = GammaClient._parse_event(raw)
        return self.analyzer.analyze_event(event)

    # ── Signal Detection ───────────────────────────────────────────────

    def detect_signals(
        self,
        limit: int = 50,
        spread_threshold: float = 0.05,
        imbalance_threshold: float = 0.3,
    ) -> dict[str, list[dict]]:
        """Scan markets for analytical signals."""
        self.signals.spread_threshold = spread_threshold
        self.signals.imbalance_threshold = imbalance_threshold

        snapshots = self.pipeline.get_tradeable_snapshots(limit=limit)
        raw_signals = self.signals.scan_snapshots(snapshots)

        return {
            mid: [
                {"type": s.signal_type, "strength": s.strength, "desc": s.description}
                for s in sigs
            ]
            for mid, sigs in raw_signals.items()
        }

    # ── Health & Status ────────────────────────────────────────────────

    def status(self) -> dict:
        """Get agent and API health status."""
        return {
            "agent": self.profile.name,
            "version": self.profile.version,
            "clob_healthy": self.clob.health(),
            "authenticated": self.config.is_authenticated,
            "llm_available": self.config.has_llm,
            "capabilities": [c.name for c in self.profile.capabilities if c.enabled],
        }

    # ── Compact Output Helpers ─────────────────────────────────────────

    @staticmethod
    def compact_json(data: Any) -> str:
        """Serialize to compact JSON (minimal token usage)."""
        return json.dumps(data, separators=(",", ":"), default=str)

    def market_summary(self, market_id: str) -> str:
        """One-line market summary for token-efficient contexts."""
        raw = self.gamma.get_market(market_id)
        m = GammaClient._parse_market(raw)
        return (
            f"{m.question} | Yes:{m.yes_price} No:{m.no_price} "
            f"| Vol:{m.volume:.0f} Liq:{m.liquidity:.0f} "
            f"| {'ACTIVE' if m.is_tradeable else 'INACTIVE'}"
        )
