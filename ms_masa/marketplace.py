"""
Ms-MASA Marketplace Integration - Smart contract and protocol hooks.

Three paths for trading Ms-MASA skills as value:

1. ON-CHAIN REGISTRY (OLAS/Autonolas pattern)
   - Register skills as on-chain service components
   - Composable with other autonomous agent services
   - Revenue via staking/bonding mechanics

2. AGENT MARKETPLACE (A2A / MCP discovery)
   - Advertise skills via Agent Cards / MCP manifests
   - Other agents discover and call Ms-MASA tools
   - Metered billing per API call

3. SKILL NFT (ERC-721/1155 pattern)
   - Mint agent configurations as composable NFTs
   - Trade specialized agent setups on-chain
   - Royalties on skill usage

This module provides the integration hooks for all three paths.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from ms_masa.skill_manifest import MANIFEST, AgentManifest, PricingTier


# ══════════════════════════════════════════════════════════════════════
# PATH 1: On-Chain Registry (OLAS / Autonolas Pattern)
# ══════════════════════════════════════════════════════════════════════

@dataclass
class OnChainServiceDescriptor:
    """
    Descriptor for registering Ms-MASA as an on-chain agent service.

    Compatible with Autonolas (OLAS) protocol:
    - Services are registered on Ethereum/Gnosis Chain
    - Components are reusable skill packages
    - Agents bond OLAS tokens to operate services
    - Revenue shared between service owners and operators

    Also applicable to:
    - Morpheus (MOR) agent marketplace
    - Fetch.ai agent registration
    - Any EVM-based agent registry
    """
    service_name: str = "ms_masa_polymarket"
    version: str = "0.1.0"
    description: str = "Polymarket prediction market intelligence service"
    chain_id: int = 100  # Gnosis Chain (OLAS default)

    # On-chain registration parameters
    agent_ids: list[int] = field(default_factory=list)
    threshold: int = 1  # Multi-sig threshold for service operation
    token_address: str = ""  # OLAS or service-specific token

    def registration_calldata(self) -> dict:
        """
        Generate the calldata for ServiceRegistry.create().

        This would be sent to the OLAS ServiceRegistry contract
        to register Ms-MASA as an autonomous service.
        """
        return {
            "contract": "ServiceRegistry",
            "method": "create",
            "params": {
                "serviceOwner": "{{DEPLOYER_ADDRESS}}",
                "configHash": self._config_hash(),
                "agentIds": self.agent_ids or [1],
                "agentParams": [[1, self.threshold]],
                "threshold": self.threshold,
            },
            "note": (
                "Deploy via: olas-cli service create --config service.yaml\n"
                "Or interact directly with ServiceRegistry on Gnosis Chain"
            ),
        }

    def component_registration(self) -> list[dict]:
        """
        Generate component registrations for each skill.

        In OLAS, components are reusable building blocks that
        services compose together.
        """
        components = []
        for skill in MANIFEST.skills:
            components.append({
                "contract": "ComponentRegistry",
                "method": "create",
                "params": {
                    "componentOwner": "{{DEPLOYER_ADDRESS}}",
                    "configHash": f"bafybei...{skill.name}",  # IPFS hash placeholder
                    "dependencies": [],
                },
                "metadata": {
                    "name": f"ms_masa_{skill.name}",
                    "description": skill.description,
                    "version": self.version,
                },
            })
        return components

    def _config_hash(self) -> str:
        """Generate a placeholder IPFS config hash."""
        return f"bafybei_ms_masa_{self.version.replace('.', '_')}"

    def staking_parameters(self) -> dict:
        """Define staking parameters for service operation."""
        return {
            "min_stake": "1000 OLAS",
            "reward_rate": "Based on service utilization",
            "slashing": "Inactive for > 24h without heartbeat",
            "unbonding_period": "7 days",
            "note": "Operators stake OLAS to run Ms-MASA service instances",
        }


# ══════════════════════════════════════════════════════════════════════
# PATH 2: Agent Marketplace (Discovery + Metered Billing)
# ══════════════════════════════════════════════════════════════════════

@dataclass
class UsageRecord:
    """Track a single skill invocation for billing."""
    skill_name: str
    caller_id: str
    timestamp: float
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0
    success: bool = True


@dataclass
class MarketplaceAdapter:
    """
    Adapter for participating in agent marketplaces.

    Handles:
    - Skill advertisement and discovery
    - Usage metering and billing
    - Rate limiting
    - Access control per caller

    Compatible with:
    - Self-hosted marketplace (simple REST API)
    - OLAS service marketplace
    - Any agent registry supporting JSON skill descriptors
    """
    manifest: AgentManifest = field(default_factory=lambda: MANIFEST)
    usage_log: list[UsageRecord] = field(default_factory=list)
    rate_limits: dict[str, int] = field(default_factory=lambda: {
        "free": 1000,       # calls per hour
        "metered": 100,     # calls per hour
        "premium": 50,      # calls per hour
    })
    callers: dict[str, dict] = field(default_factory=dict)

    def advertise(self) -> dict:
        """
        Generate the full marketplace advertisement.

        This is what other agents see when discovering Ms-MASA.
        """
        return {
            "agent": {
                "name": self.manifest.name,
                "version": self.manifest.version,
                "description": self.manifest.description,
            },
            "skills": {
                s.name: {
                    "description": s.description,
                    "category": s.category,
                    "pricing": s.pricing.value,
                    "requires_auth": s.requires_auth,
                    "requires_api": s.requires_api,
                    "tags": s.tags,
                    "examples": s.examples,
                }
                for s in self.manifest.skills
            },
            "pricing": self.manifest.pricing_summary(),
            "protocols": self.manifest.protocols,
            "endpoints": {
                "mcp": "stdio://python -m ms_masa.mcp_server",
                "a2a": "/.well-known/agent.json",
                "rest": "/api/v1/skills",
            },
        }

    def authorize_caller(self, caller_id: str, tier: str = "free") -> dict:
        """Register a caller with a specific tier."""
        self.callers[caller_id] = {
            "tier": tier,
            "registered": time.time(),
            "calls_this_hour": 0,
            "hour_start": time.time(),
        }
        return {"caller_id": caller_id, "tier": tier, "status": "authorized"}

    def check_rate_limit(self, caller_id: str) -> bool:
        """Check if caller is within rate limits."""
        caller = self.callers.get(caller_id)
        if not caller:
            return False

        now = time.time()
        if now - caller["hour_start"] > 3600:
            caller["calls_this_hour"] = 0
            caller["hour_start"] = now

        limit = self.rate_limits.get(caller["tier"], 0)
        return caller["calls_this_hour"] < limit

    def record_usage(self, skill_name: str, caller_id: str, **kwargs) -> UsageRecord:
        """Record a skill invocation."""
        record = UsageRecord(
            skill_name=skill_name,
            caller_id=caller_id,
            timestamp=time.time(),
            **kwargs,
        )
        self.usage_log.append(record)

        caller = self.callers.get(caller_id)
        if caller:
            caller["calls_this_hour"] += 1

        return record

    def billing_summary(self, caller_id: Optional[str] = None) -> dict:
        """Generate a billing summary."""
        records = self.usage_log
        if caller_id:
            records = [r for r in records if r.caller_id == caller_id]

        by_skill: dict[str, int] = {}
        for r in records:
            by_skill[r.skill_name] = by_skill.get(r.skill_name, 0) + 1

        return {
            "total_calls": len(records),
            "by_skill": by_skill,
            "successful": sum(1 for r in records if r.success),
            "failed": sum(1 for r in records if not r.success),
        }

    def well_known_agent_json(self) -> dict:
        """
        Generate /.well-known/agent.json for A2A discovery.

        Per the Google A2A spec, agents advertise themselves at this
        well-known URL so other agents can discover them.
        """
        return self.manifest.to_a2a_agent_card()


# ══════════════════════════════════════════════════════════════════════
# PATH 3: Skill NFT (On-Chain Composable Agent Configs)
# ══════════════════════════════════════════════════════════════════════

@dataclass
class SkillNFTMetadata:
    """
    ERC-721/1155 metadata for a tradeable agent configuration.

    Pattern: Mint specialized agent configs as NFTs that:
    - Encode specific skill combinations + parameters
    - Are tradeable on OpenSea / Blur / any NFT marketplace
    - Include royalties on secondary sales
    - Can be "equipped" by agent frameworks to gain capabilities

    This is the "trading skills as value" path.
    """
    name: str = ""
    description: str = ""
    image: str = ""  # IPFS URI for visual representation
    external_url: str = ""

    # Agent configuration encoded in the NFT
    skills: list[str] = field(default_factory=list)
    agent_type: str = "read_only_agent"
    parameters: dict = field(default_factory=dict)

    # On-chain attributes for marketplace filtering
    attributes: list[dict] = field(default_factory=list)

    def to_erc721_metadata(self) -> dict:
        """Standard ERC-721 metadata JSON (OpenSea compatible)."""
        return {
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "external_url": self.external_url,
            "attributes": self.attributes + [
                {"trait_type": "Agent Type", "value": self.agent_type},
                {"trait_type": "Skill Count", "value": len(self.skills)},
                {"trait_type": "Platform", "value": "Polymarket"},
                {"trait_type": "Framework", "value": "Ms-MASA"},
            ],
            "properties": {
                "skills": self.skills,
                "agent_type": self.agent_type,
                "parameters": self.parameters,
                "ms_masa_version": "0.1.0",
            },
        }


# ── Pre-built NFT configurations ──────────────────────────────────────

SKILL_NFT_TEMPLATES = {
    "market_sentinel": SkillNFTMetadata(
        name="Ms-MASA: Market Sentinel",
        description=(
            "Autonomous market monitoring agent. Scans Polymarket for price "
            "movements, volume spikes, and liquidity changes. Includes signal "
            "detection for spreads, imbalances, and near-certainty events."
        ),
        skills=["scan_markets", "detect_signals", "analyze_market"],
        agent_type="analytical_agent",
        parameters={
            "scan_interval": 60,
            "spread_threshold": 0.05,
            "alert_channels": ["webhook"],
        },
        attributes=[
            {"trait_type": "Rarity", "value": "Common"},
            {"trait_type": "Category", "value": "Monitoring"},
        ],
    ),
    "alpha_hunter": SkillNFTMetadata(
        name="Ms-MASA: Alpha Hunter",
        description=(
            "Advanced signal detection agent. Combines order book analysis, "
            "liquidity scoring, and multi-market correlation to identify "
            "alpha opportunities in prediction markets."
        ),
        skills=["scan_markets", "detect_signals", "analyze_market", "search_markets", "ecosystem_reference"],
        agent_type="analytical_agent",
        parameters={
            "scan_interval": 30,
            "spread_threshold": 0.03,
            "imbalance_threshold": 0.2,
            "multi_market_correlation": True,
        },
        attributes=[
            {"trait_type": "Rarity", "value": "Rare"},
            {"trait_type": "Category", "value": "Alpha"},
        ],
    ),
    "full_stack_specialist": SkillNFTMetadata(
        name="Ms-MASA: Full Stack Specialist",
        description=(
            "Complete Polymarket intelligence suite. All knowledge, data, "
            "analysis, signal, and builder capabilities. The definitive "
            "Polymarket agent toolkit."
        ),
        skills=[s.name for s in MANIFEST.skills],
        agent_type="trading_agent",
        parameters={
            "all_capabilities": True,
            "builder_enabled": True,
        },
        attributes=[
            {"trait_type": "Rarity", "value": "Legendary"},
            {"trait_type": "Category", "value": "Full Suite"},
        ],
    ),
}


# ══════════════════════════════════════════════════════════════════════
# INSTALLATION DIRECTIONS
# ══════════════════════════════════════════════════════════════════════

INSTALLATION_GUIDE = {
    "mcp_claude_desktop": {
        "title": "Install into Claude Desktop (MCP)",
        "steps": [
            "1. pip install ms-masa",
            '2. Add to ~/Library/Application Support/Claude/claude_desktop_config.json:',
            '   {"mcpServers": {"ms-masa": {"command": "python", "args": ["-m", "ms_masa.mcp_server"]}}}',
            "3. Restart Claude Desktop",
            "4. Ms-MASA tools appear in Claude's tool palette",
        ],
    },
    "mcp_claude_code": {
        "title": "Install into Claude Code (MCP)",
        "steps": [
            "1. pip install ms-masa",
            "2. Add to .claude/settings.json or .mcp.json:",
            '   {"mcpServers": {"ms-masa": {"command": "python", "args": ["-m", "ms_masa.mcp_server"]}}}',
            "3. Claude Code auto-discovers Ms-MASA tools",
        ],
    },
    "langchain": {
        "title": "Install into LangChain / LangGraph",
        "steps": [
            "1. pip install ms-masa",
            "2. In your agent code:",
            "   from ms_masa.integrations import langchain_tools",
            "   tools = langchain_tools()",
            "   agent = create_react_agent(llm, tools)",
        ],
    },
    "crewai": {
        "title": "Install into CrewAI",
        "steps": [
            "1. pip install ms-masa",
            "2. In your crew definition:",
            "   from ms_masa.integrations import crewai_tools",
            "   polymarket_agent = Agent(",
            '       role="Polymarket Analyst",',
            "       tools=crewai_tools(),",
            "   )",
        ],
    },
    "autogen": {
        "title": "Install into AutoGen",
        "steps": [
            "1. pip install ms-masa",
            "2. Register as function tools:",
            "   from ms_masa.integrations import autogen_functions",
            "   assistant.register_for_llm(description='...')(autogen_functions())",
        ],
    },
    "olas": {
        "title": "Deploy as OLAS Autonomous Service",
        "steps": [
            "1. pip install ms-masa open-autonomy",
            "2. Generate service config: python -m ms_masa.marketplace olas-config",
            "3. Register components on-chain: autonomy push-all",
            "4. Register service: autonomy mint --use-custom-chain",
            "5. Stake OLAS tokens to activate service",
        ],
    },
    "a2a": {
        "title": "Advertise via Google A2A Protocol",
        "steps": [
            "1. pip install ms-masa",
            "2. Host agent card at /.well-known/agent.json",
            "3. python -m ms_masa.marketplace a2a-card > agent.json",
            "4. Other A2A agents discover Ms-MASA via agent card URL",
        ],
    },
    "direct_python": {
        "title": "Direct Python Import",
        "steps": [
            "1. pip install ms-masa",
            "2. from ms_masa import MsMasaAgent",
            "3. agent = MsMasaAgent()",
            '4. agent.explain("platform")  # Zero API calls',
            '5. agent.scan_markets(limit=20)  # Live data',
        ],
    },
}


# ── CLI for marketplace operations ────────────────────────────────────

def main():
    """CLI for marketplace integration tasks."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Ms-MASA Marketplace Integration")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("advertise", help="Print full marketplace advertisement")
    sub.add_parser("a2a-card", help="Print A2A agent card JSON")
    sub.add_parser("mcp-config", help="Print MCP server config for Claude")
    sub.add_parser("olas-config", help="Print OLAS service descriptor")
    sub.add_parser("nft-metadata", help="Print Skill NFT metadata templates")
    sub.add_parser("install-guide", help="Print installation guide for all platforms")
    sub.add_parser("pricing", help="Print pricing summary")
    sub.add_parser("langchain-tools", help="Print LangChain tool definitions")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    adapter = MarketplaceAdapter()

    if args.command == "advertise":
        print(json.dumps(adapter.advertise(), indent=2))

    elif args.command == "a2a-card":
        print(json.dumps(MANIFEST.to_a2a_agent_card(), indent=2))

    elif args.command == "mcp-config":
        print(json.dumps(MANIFEST.to_mcp_manifest(), indent=2))

    elif args.command == "olas-config":
        print(json.dumps(MANIFEST.to_olas_registry(), indent=2))

    elif args.command == "nft-metadata":
        for name, nft in SKILL_NFT_TEMPLATES.items():
            print(f"\n{'='*60}")
            print(f"Template: {name}")
            print(json.dumps(nft.to_erc721_metadata(), indent=2))

    elif args.command == "install-guide":
        for key, guide in INSTALLATION_GUIDE.items():
            print(f"\n{'─'*60}")
            print(f"  {guide['title']}")
            print(f"{'─'*60}")
            for step in guide["steps"]:
                print(f"  {step}")
        print()

    elif args.command == "pricing":
        print(json.dumps(MANIFEST.pricing_summary(), indent=2))

    elif args.command == "langchain-tools":
        print(json.dumps(MANIFEST.to_langchain_toolkit(), indent=2))


if __name__ == "__main__":
    main()
