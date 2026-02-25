"""
Polymarket Knowledge Base - compressed reference for low-token agent use.

This module encodes the complete Polymarket platform knowledge into
structured, quickly-retrievable formats optimized for LLM consumption.
Designed for minimal token usage while maximizing information density.
"""

from __future__ import annotations

from typing import Optional


class PolymarketKB:
    """Compressed knowledge base of the Polymarket platform."""

    # ── Platform Architecture ──────────────────────────────────────────

    PLATFORM = {
        "name": "Polymarket",
        "type": "Prediction Market (Binary Outcomes)",
        "chain": "Polygon (chain_id=137)",
        "token": "USDC (6 decimals)",
        "framework": "Gnosis Conditional Token Framework (CTF)",
        "token_standard": "ERC-1155 conditional tokens",
        "settlement": "On-chain, non-custodial via hybrid-decentralized exchange",
        "price_range": "0.00 - 1.00 (probability-based)",
        "outcomes": "Binary (Yes/No) resolved via UMA oracle",
    }

    # ── API Ecosystem ──────────────────────────────────────────────────

    APIS = {
        "gamma": {
            "base": "https://gamma-api.polymarket.com",
            "purpose": "Market discovery, metadata, events",
            "auth": "None (public)",
            "endpoints": {
                "/markets": "List/filter markets (active, closed, archived, tag, slug, limit, offset)",
                "/markets/{id}": "Single market detail",
                "/events": "List/filter events",
                "/events/{id}": "Single event detail",
            },
            "key_fields": {
                "outcomePrices": "JSON string of [yes_price, no_price]",
                "clobTokenIds": "JSON string of [yes_token, no_token]",
                "conditionId": "CTF condition identifier",
                "enableOrderBook": "Whether CLOB trading is active",
            },
        },
        "clob": {
            "base": "https://clob.polymarket.com",
            "purpose": "Order book, trading, price feeds",
            "auth_levels": {
                "L0": "Public - market data, prices, order books",
                "L1": "Authenticated - order placement, cancellation, trade history",
            },
            "public_endpoints": {
                "/": "Health check",
                "/time": "Server timestamp",
                "/midpoint": "Mid-market price (token_id)",
                "/price": "Best price for side (token_id, side)",
                "/book": "Full order book (token_id)",
                "/books": "Multiple order books",
                "/simplified-markets": "Compact market list",
                "/last-trade-price": "Last trade price (token_id)",
            },
            "auth_endpoints": {
                "POST /order": "Place order",
                "DELETE /order": "Cancel order",
                "DELETE /orders": "Cancel all orders",
                "GET /orders": "List open orders",
                "GET /trades": "Trade history",
            },
        },
    }

    # ── Order Types ────────────────────────────────────────────────────

    ORDER_TYPES = {
        "GTC": "Good-Till-Cancelled: Persists until manually cancelled",
        "FOK": "Fill-or-Kill: Execute immediately in full or reject entirely",
        "GTD": "Good-Till-Date: Expires at specified timestamp",
        "FAK": "Fill-and-Kill: Fill what's available, cancel remainder",
    }

    # ── Authentication ─────────────────────────────────────────────────

    AUTH = {
        "signature_types": {
            0: "EOA: Standard wallet (MetaMask, hardware)",
            1: "POLY_PROXY: Email/Magic wallet delegated signing",
            2: "POLY_GNOSIS: Browser wallet proxy signatures",
        },
        "credential_flow": [
            "1. Initialize ClobClient with private_key, chain_id=137, signature_type",
            "2. Call create_or_derive_api_creds() to get api_key, api_secret, api_passphrase",
            "3. Call set_api_creds() to attach credentials to client",
            "4. For EOA: Approve USDC + CTF token allowances to exchange contracts",
        ],
        "approval_contracts": [
            "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E (Exchange)",
            "0xC5d563A36AE78145C45a50134d48A1215220f80a (Neg Risk Exchange)",
            "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296 (Neg Risk Adapter)",
        ],
        "token_contracts": {
            "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "CTF": "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",
        },
    }

    # ── SDK/Libraries ──────────────────────────────────────────────────

    SDKS = {
        "py-clob-client": {
            "install": "pip install py-clob-client",
            "purpose": "Python SDK for CLOB API (orders, books, prices)",
            "key_classes": ["ClobClient", "OrderArgs", "MarketOrderArgs"],
            "key_methods": [
                "get_simplified_markets()", "get_order_book(token_id)",
                "get_midpoint(token_id)", "get_price(token_id, side)",
                "create_order(OrderArgs)", "create_market_order(MarketOrderArgs)",
                "post_order(signed_order, OrderType)", "cancel(order_id)",
                "cancel_all()", "get_orders()", "get_trades()",
                "create_or_derive_api_creds()", "set_api_creds(creds)",
            ],
        },
        "clob-client": {
            "install": "npm install @polymarket/clob-client",
            "purpose": "TypeScript SDK for CLOB API",
        },
        "py-order-utils": {
            "install": "pip install polymarket-order-utils",
            "purpose": "Order signing and construction utilities",
            "key_classes": ["OrderBuilder", "Signer"],
        },
        "agents": {
            "repo": "github.com/Polymarket/agents",
            "purpose": "AI agent framework for autonomous trading",
            "modules": {
                "polymarket/gamma.py": "GammaMarketClient - market discovery",
                "polymarket/polymarket.py": "Polymarket - full API integration",
                "application/trade.py": "Trader - autonomous trading logic",
                "connectors/chroma.py": "Vector DB for RAG-based analysis",
            },
            "agent_flow": [
                "1. Discover events via Gamma API",
                "2. Filter tradeable markets",
                "3. Gather context (news, web, historical data)",
                "4. Send to LLM for analysis",
                "5. Generate trade decision",
                "6. Build and sign order",
                "7. Execute via CLOB API",
            ],
        },
    }

    # ── Smart Contracts ────────────────────────────────────────────────

    CONTRACTS = {
        "ctf_exchange": {
            "address": "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",
            "purpose": "Atomic swaps between CTF ERC1155 and ERC20 collateral",
            "model": "Hybrid-decentralized: offchain matching, onchain settlement",
            "audit": "Chainsecurity",
        },
        "neg_risk_exchange": {
            "address": "0xC5d563A36AE78145C45a50134d48A1215220f80a",
            "purpose": "Exchange for neg-risk (complementary outcome) markets",
        },
        "conditional_tokens": {
            "address": "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",
            "standard": "ERC-1155",
            "purpose": "Represents market outcome positions",
        },
    }

    # ── Market Structure ───────────────────────────────────────────────

    MARKET_STRUCTURE = {
        "hierarchy": "Platform > Events > Markets > Outcomes > Tokens",
        "event": "Groups related markets (e.g., 'US Election 2024')",
        "market": "Single question with binary outcomes (Yes/No)",
        "outcome": "Each outcome has a CLOB token_id for trading",
        "price_meaning": "Price = implied probability (0.50 = 50% chance)",
        "complementary": "Yes price + No price ~= 1.00 (minus spread)",
        "neg_risk": "Markets where outcomes are mutually exclusive within event",
        "resolution": "Markets resolve to 1.00 (correct) or 0.00 (incorrect) via oracle",
        "tick_sizes": ["0.1", "0.01", "0.001", "0.0001"],
    }

    # ── Agent Building Patterns ────────────────────────────────────────

    AGENT_PATTERNS = {
        "read_only_agent": {
            "description": "Monitor markets, analyze data, generate insights",
            "requires": "No auth (Gamma + CLOB public endpoints)",
            "capabilities": [
                "Market discovery and filtering",
                "Order book analysis",
                "Price monitoring and alerts",
                "Event tracking",
                "Liquidity analysis",
            ],
        },
        "analytical_agent": {
            "description": "Deep market analysis with LLM reasoning",
            "requires": "OpenAI API key (or compatible LLM)",
            "capabilities": [
                "All read-only capabilities",
                "LLM-powered market assessment",
                "News and context integration",
                "Signal generation",
                "RAG-based research",
            ],
        },
        "trading_agent": {
            "description": "Full autonomous trading (requires authorization)",
            "requires": "Polygon wallet + CLOB API credentials",
            "capabilities": [
                "All analytical capabilities",
                "Order placement and management",
                "Position tracking",
                "Risk management",
                "Portfolio balancing",
            ],
        },
    }

    # ── Query Interface ────────────────────────────────────────────────

    @classmethod
    def lookup(cls, topic: str) -> dict | str | None:
        """Quick-lookup any topic in the knowledge base."""
        topic_lower = topic.lower().strip()

        topic_map = {
            "platform": cls.PLATFORM,
            "apis": cls.APIS,
            "api": cls.APIS,
            "gamma": cls.APIS["gamma"],
            "clob": cls.APIS["clob"],
            "orders": cls.ORDER_TYPES,
            "order_types": cls.ORDER_TYPES,
            "auth": cls.AUTH,
            "authentication": cls.AUTH,
            "sdks": cls.SDKS,
            "libraries": cls.SDKS,
            "contracts": cls.CONTRACTS,
            "smart_contracts": cls.CONTRACTS,
            "market_structure": cls.MARKET_STRUCTURE,
            "structure": cls.MARKET_STRUCTURE,
            "patterns": cls.AGENT_PATTERNS,
            "agent_patterns": cls.AGENT_PATTERNS,
        }

        return topic_map.get(topic_lower)

    @classmethod
    def get_agent_context(cls, agent_type: str = "read_only_agent") -> str:
        """Get a compact context string for an agent, optimized for token efficiency."""
        lines = [
            f"POLYMARKET: {cls.PLATFORM['type']} on {cls.PLATFORM['chain']}",
            f"Price=probability(0-1), Token={cls.PLATFORM['token']}, Settlement={cls.PLATFORM['settlement']}",
            f"Structure: {cls.MARKET_STRUCTURE['hierarchy']}",
            f"Gamma API: {cls.APIS['gamma']['base']} (discovery, no auth)",
            f"CLOB API: {cls.APIS['clob']['base']} (books/trading, L0=public L1=auth)",
            "Orders: " + ", ".join(k + "=" + v.split(":")[0] for k, v in cls.ORDER_TYPES.items()),
        ]

        pattern = cls.AGENT_PATTERNS.get(agent_type, cls.AGENT_PATTERNS["read_only_agent"])
        lines.append(f"Agent type: {pattern['description']}")
        lines.append(f"Requires: {pattern['requires']}")

        return "\n".join(lines)

    @classmethod
    def topics(cls) -> list[str]:
        """List all available knowledge base topics."""
        return [
            "platform", "apis", "gamma", "clob", "orders",
            "auth", "sdks", "contracts", "market_structure", "patterns",
        ]
