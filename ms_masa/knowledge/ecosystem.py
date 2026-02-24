"""
Complete Polymarket Ecosystem Reference.

Ultra-dense reference of the full Polymarket developer ecosystem,
including all repos, contracts, APIs, WebSocket streams, RFQ system,
fee structure, and resolution mechanics.

Sourced from: github.com/Polymarket (all public repos)
"""

from __future__ import annotations


class EcosystemReference:
    """Complete Polymarket ecosystem reference data."""

    # ── Repository Map ─────────────────────────────────────────────────

    REPOS = {
        "py-clob-client": {"lang": "Python", "purpose": "Python SDK for CLOB trading", "install": "pip install py-clob-client"},
        "clob-client": {"lang": "TypeScript", "purpose": "TypeScript SDK for CLOB trading", "install": "npm install @polymarket/clob-client"},
        "rs-clob-client": {"lang": "Rust", "purpose": "Rust SDK with type-safe state machine", "install": 'polymarket-client-sdk = "0.3"'},
        "agents": {"lang": "Python", "purpose": "AI agent framework for autonomous trading"},
        "ctf-exchange": {"lang": "Solidity", "purpose": "Core exchange smart contracts (Foundry)"},
        "uma-ctf-adapter": {"lang": "Solidity", "purpose": "UMA oracle resolution adapter"},
        "neg-risk-ctf-adapter": {"lang": "Solidity", "purpose": "Multi-outcome market adapter"},
        "polymarket-subgraph": {"lang": "TypeScript", "purpose": "GraphQL indexing of on-chain data"},
        "polymarket-cli": {"lang": "Rust", "purpose": "Command-line trading tool"},
        "py-builder-relayer-client": {"lang": "Python", "purpose": "Gasless relayer API client"},
    }

    # ── WebSocket Streaming ────────────────────────────────────────────

    WEBSOCKET = {
        "market_url": "wss://ws-subscriptions-clob.polymarket.com/ws/market",
        "user_url": "wss://ws-subscriptions-clob.polymarket.com/ws/user",
        "channels": {
            "orderbook": {"auth": False, "data": "Bid/ask level updates per asset"},
            "prices": {"auth": False, "data": "Price change notifications"},
            "midpoints": {"auth": False, "data": "Calculated midpoint updates"},
            "orders": {"auth": True, "data": "User order state changes"},
            "trades": {"auth": True, "data": "User trade executions"},
        },
    }

    # ── Fee Structure ──────────────────────────────────────────────────

    FEES = {
        "formula": "fee = baseRate * min(price, 1 - price) * quantity",
        "symmetry": "Selling 100@0.99 = same fee as buying 100 complement@0.01",
        "max_rate_bps": 1000,  # 10%
        "per_market": "Each market has its own fee_rate_bps",
        "query": "GET /fee-rate?token_id=X",
        "buy_deduction": "Deducted from received tokens",
        "sell_deduction": "Deducted from USDC proceeds",
    }

    # ── Resolution Mechanics ───────────────────────────────────────────

    RESOLUTION = {
        "oracle": "UMA Optimistic Oracle",
        "flow": [
            "1. Market initialized, condition prepared on CTF",
            "2. Resolution request submitted to UMA Oracle",
            "3. Proposer submits proposed resolution (~2 hour window)",
            "4. If uncontested, data becomes available",
            "5. First dispute: automatic RESET (new oracle request)",
            "6. Second dispute: escalation to UMA DVM (48-72 hours)",
            "7. resolve() called, CTF condition resolved",
            "8. Winners redeem tokens for USDC",
        ],
        "outcomes_binary": {
            "yes_wins": "[1, 0]",
            "no_wins": "[0, 1]",
        },
    }

    # ── Neg-Risk Multi-Outcome ─────────────────────────────────────────

    NEG_RISK = {
        "purpose": "Multi-outcome events (e.g., elections with 3+ candidates)",
        "mechanism": "Each candidate gets binary YES/NO market, exactly ONE resolves YES",
        "identity": "1 NO(A) + 1 NO(B) = 1 USDC + 1 YES(C)",
        "contracts": {
            "NegRiskAdapter": "Converts NO positions to YES + USDC",
            "NegRiskOperator": "Admin: market preparation, oracle integration",
            "WrappedCollateral": "Wraps USDC for separate management",
            "Vault": "Accumulates USDC + YES tokens as conversion fees",
            "NegRiskCTFExchange": "0xC5d563A36AE78145C45a50134d48A1215220f80a",
        },
        "constraint": "Markets MUST resolve with exactly one YES outcome",
    }

    # ── Complete CLOB Endpoints ────────────────────────────────────────

    CLOB_ENDPOINTS = {
        "public": {
            "GET /": "Health check",
            "GET /time": "Server timestamp",
            "GET /sampling-simplified-markets": "Sample simplified markets",
            "GET /sampling-markets": "Sample full markets",
            "GET /simplified-markets": "All simplified markets (paginated)",
            "GET /markets": "All full markets (paginated)",
            "GET /markets/{condition_id}": "Single market by condition ID",
            "GET /book?token_id=X": "Order book for token",
            "GET /books": "Multiple order books",
            "GET /midpoint?token_id=X": "Midpoint price",
            "GET /midpoints": "Multiple midpoints",
            "GET /price?token_id=X&side=Y": "Best price for side",
            "GET /prices": "Multiple prices",
            "GET /spread?token_id=X": "Bid-ask spread",
            "GET /spreads": "Multiple spreads",
            "GET /last-trade-price?token_id=X": "Last trade price",
            "GET /last-trades-prices": "Multiple last trade prices",
            "GET /tick-size?token_id=X": "Market tick size",
            "GET /neg-risk?token_id=X": "Whether market uses neg-risk",
            "GET /fee-rate?token_id=X": "Fee rate in bps",
            "GET /prices-history": "Historical prices",
            "GET /live-activity/events/{id}": "Live event activity",
        },
        "authenticated": {
            "POST /order": "Place single order (L2)",
            "POST /orders": "Place batch orders (L2)",
            "GET /data/order/{id}": "Get order by ID (L2)",
            "GET /data/orders": "List orders (L2)",
            "DELETE /order": "Cancel single order (L2)",
            "DELETE /orders": "Cancel batch orders (L2)",
            "DELETE /cancel-all": "Cancel all orders (L2)",
            "DELETE /cancel-market-orders": "Cancel orders for market (L2)",
            "GET /data/trades": "Trade history (L2)",
            "GET /balance-allowance": "Balance query (L2)",
            "POST /balance-allowance/update": "Update allowance (L2)",
            "GET /notifications": "Get notifications (L2)",
            "DELETE /notifications": "Dismiss notifications (L2)",
            "GET /order-scoring": "Single order reward eligibility (L2)",
            "GET /orders-scoring": "Batch order scoring (L2)",
            "POST /v1/heartbeats": "Keep-alive heartbeat (L2)",
        },
        "auth_keys": {
            "POST /auth/api-key": "Create API key (L1)",
            "GET /auth/api-keys": "List API keys (L2)",
            "GET /auth/derive-api-key": "Derive API key (L1)",
            "DELETE /auth/api-key": "Delete API key (L2)",
            "POST /auth/readonly-api-key": "Create readonly key (L2)",
            "GET /auth/readonly-api-keys": "List readonly keys (L2)",
            "DELETE /auth/readonly-api-key": "Delete readonly key (L2)",
            "POST /auth/builder-api-key": "Create builder key (L2)",
        },
        "rewards": {
            "GET /rewards/user": "User rewards (L2)",
            "GET /rewards/user/total": "Total user rewards (L2)",
            "GET /rewards/user/percentages": "Reward percentages (L2)",
            "GET /rewards/markets/current": "Current market rewards (public)",
            "GET /rewards/markets/{id}": "Market rewards by ID (public)",
        },
        "rfq": {
            "POST /rfq/request": "Create RFQ request (L2)",
            "POST /rfq/quote": "Submit quote (L2)",
            "GET /rfq/data/requests": "List RFQ requests (L2)",
            "GET /rfq/data/best-quote": "Best quote for request (L2)",
            "POST /rfq/request/accept": "Accept RFQ quote (L2)",
            "POST /rfq/quote/approve": "Approve RFQ quote (L2)",
            "GET /rfq/config": "RFQ configuration (public)",
        },
        "pagination": {
            "initial_cursor": "MA== (base64 '0')",
            "end_cursor": "LTE= (base64 '-1')",
            "param": "next_cursor",
        },
    }

    # ── EIP-712 Order Structure ────────────────────────────────────────

    ORDER_STRUCTURE = {
        "fields": {
            "salt": "uint256 - Random nonce for uniqueness",
            "maker": "address - Funder address (holds funds)",
            "signer": "address - Signing key address",
            "taker": "address - 0x0 for any taker, or specific",
            "tokenId": "uint256 - CTF ERC1155 token ID",
            "makerAmount": "uint256 - Amount maker provides",
            "takerAmount": "uint256 - Amount taker provides",
            "expiration": "uint256 - 0 = no expiration",
            "nonce": "uint256 - Replay protection",
            "feeRateBps": "uint256 - Fee rate in basis points",
            "side": "uint8 - 0=BUY, 1=SELL",
            "signatureType": "uint8 - 0=EOA, 1=POLY_PROXY, 2=POLY_GNOSIS",
        },
        "matching_scenarios": {
            "NORMAL": "Direct token-for-collateral swap",
            "MINT": "Both buying complementary -> splitPosition() mints from collateral",
            "MERGE": "Both selling complementary -> mergePositions() burns to collateral",
        },
    }

    # ── Subgraph Indexes ───────────────────────────────────────────────

    SUBGRAPHS = {
        "activity": "User trading activity",
        "fpmm": "Fixed Product Market Maker (AMM) data",
        "oi": "Open interest",
        "orderbook": "Order book events",
        "pnl": "Profit and loss tracking",
        "polymarket": "Core market/event data",
        "sports-oracle": "Sports oracle data",
    }

    # ── Agent Framework Prompts ────────────────────────────────────────

    AGENT_PROMPTS = {
        "simple_trader": "Basic buy/sell decision with amount",
        "market_analyst": "Probability estimation for event outcomes",
        "sentiment_analyzer": "News article scoring 0-1",
        "routing": "Direct questions to appropriate data sources",
        "multiquery": "Generate 5 alternative phrasings for vector search",
        "superforecaster": "Systematic: decomposition, base rates, factors, probability",
        "one_best_trade": "Specific: price, size %, BUY/SELL recommendation",
        "event_filter": "Identify most profitable trading opportunities",
        "market_creation": "Generate novel prediction markets (6+ month expiry)",
    }

    @classmethod
    def summary(cls) -> str:
        """One-paragraph ecosystem summary for agent context."""
        return (
            "Polymarket is a hybrid-decentralized prediction market on Polygon using "
            "Gnosis CTF (ERC-1155) for outcome tokens and USDC collateral. The CLOB at "
            "clob.polymarket.com handles off-chain matching with on-chain settlement via "
            "signed EIP-712 orders. Gamma API at gamma-api.polymarket.com provides market "
            "discovery. SDKs available in Python (py-clob-client), TypeScript (@polymarket/"
            "clob-client), and Rust (polymarket-client-sdk). The agents framework at "
            "github.com/Polymarket/agents provides LLM-powered autonomous trading with "
            "RAG via ChromaDB. Markets resolve via UMA Optimistic Oracle. Neg-risk adapter "
            "enables multi-outcome events. WebSocket streaming available for real-time data. "
            "Fee = baseRate * min(price, 1-price) * quantity."
        )
