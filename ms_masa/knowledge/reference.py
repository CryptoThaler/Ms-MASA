"""
Quick Reference - ultra-compact reference cards for Polymarket operations.

Designed for minimal token use when agents need operational guidance.
Each method returns a focused, concise reference string.
"""

from __future__ import annotations


class QuickReference:
    """Ultra-compact reference cards for Polymarket operations."""

    @staticmethod
    def gamma_api() -> str:
        return """GAMMA API REFERENCE
Base: https://gamma-api.polymarket.com
Auth: None required

GET /markets?active=true&closed=false&limit=100&offset=0
  -> [{id, question, conditionId, slug, outcomes, outcomePrices(json), clobTokenIds(json), volume, liquidity, enableOrderBook, active, closed, archived, negRisk, tags}]

GET /markets/{id} -> single market object

GET /events?active=true&closed=false&limit=100
  -> [{id, title, slug, markets[], active, closed, archived, restricted, tags}]

GET /events/{id} -> single event with nested markets

Filters: active, closed, archived (bool), tag, slug (str), limit, offset (int), order (str), ascending (bool)
Note: outcomePrices and clobTokenIds are JSON-encoded strings, must parse."""

    @staticmethod
    def clob_api() -> str:
        return """CLOB API REFERENCE
Base: https://clob.polymarket.com
Auth: L0=public, L1=API key+secret+passphrase

PUBLIC (L0):
  GET /           -> health check
  GET /time       -> server timestamp
  GET /midpoint?token_id=X       -> {mid: 0.XX}
  GET /price?token_id=X&side=BUY -> {price: 0.XX}
  GET /book?token_id=X           -> {bids:[{price,size}], asks:[{price,size}], spread, ...}
  GET /simplified-markets        -> compact market list
  GET /last-trade-price?token_id=X -> {price: 0.XX}

AUTHENTICATED (L1):
  POST   /order   -> place order (signed order body + orderType)
  DELETE /order/{id} -> cancel specific order
  DELETE /orders  -> cancel all orders
  GET    /orders  -> list open orders
  GET    /trades  -> trade history

Prices: 0.00-1.00 (probability). Chain: Polygon (137). Token: USDC."""

    @staticmethod
    def order_flow() -> str:
        return """ORDER FLOW REFERENCE
1. LIMIT ORDER:
   args = OrderArgs(token_id, price, size, side=BUY|SELL)
   signed = client.create_order(args)
   result = client.post_order(signed, OrderType.GTC)

2. MARKET ORDER:
   args = MarketOrderArgs(token_id, amount, side=BUY|SELL)
   signed = client.create_market_order(args)
   result = client.post_order(signed, OrderType.FOK)

3. CANCEL:
   client.cancel(order_id)  # single
   client.cancel_all()      # all open orders

OrderTypes: GTC(persist), FOK(fill-or-kill), GTD(expiring), FAK(partial-fill)
Tick sizes: 0.1, 0.01, 0.001, 0.0001"""

    @staticmethod
    def auth_setup() -> str:
        return """AUTH SETUP REFERENCE
1. INIT CLIENT:
   client = ClobClient("https://clob.polymarket.com", key=PRIVATE_KEY, chain_id=137, signature_type=0)

2. DERIVE CREDENTIALS:
   creds = client.create_or_derive_api_creds()
   client.set_api_creds(creds)

3. APPROVE TOKENS (EOA only, one-time):
   Approve USDC (0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174) to:
     - Exchange:   0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E
     - NegRisk:    0xC5d563A36AE78145C45a50134d48A1215220f80a
     - Adapter:    0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296
   Approve CTF (0x4D97DCd97eC945f40cF65F87097ACe5EA0476045) to same 3 contracts.

Signature types: 0=EOA, 1=Magic/Email proxy, 2=Gnosis proxy
Funder param = address holding funds (differs from signing key for proxy wallets)"""

    @staticmethod
    def agent_architecture() -> str:
        return """AGENT ARCHITECTURE REFERENCE
Source: github.com/Polymarket/agents

MODULES:
  polymarket/gamma.py     -> GammaMarketClient (discovery)
  polymarket/polymarket.py -> Polymarket (full API + Web3)
  application/trade.py    -> Trader (autonomous decision loop)
  connectors/chroma.py    -> Vector DB for RAG

AGENT LOOP:
  1. get_all_tradeable_events() via Gamma API
  2. filter_events_with_rag() using vector DB context
  3. Map events -> markets -> order books
  4. source_best_trade() with LLM analysis
  5. format_trade_prompt_for_execution()
  6. execute_order() via CLOB API

DATA FLOW: Gamma(discovery) -> CLOB(books) -> LLM(analysis) -> CLOB(execution)

DEPENDENCIES: py-clob-client, py-order-utils, httpx, web3, openai, chromadb"""

    @staticmethod
    def market_concepts() -> str:
        return """POLYMARKET CONCEPTS
- Event: Groups related questions (e.g., "2024 Election")
- Market: Single yes/no question with CLOB
- Token: ERC-1155 conditional token per outcome
- Price: 0.00-1.00 = implied probability
- Yes+No ~= 1.00 (minus spread)
- Resolution: Oracle resolves to 1.00 (correct) or 0.00 (wrong)
- NegRisk: Mutually exclusive outcomes within single event
- CTF: Conditional Token Framework (Gnosis) - positions as ERC-1155
- CLOB: Central Limit Order Book - matching engine
- Spread: Ask - Bid (market maker profit / cost)
- Midpoint: (Bid + Ask) / 2 (fair value estimate)
- Depth: Total size at all price levels (liquidity indicator)"""

    @staticmethod
    def all_references() -> str:
        """Return all reference cards concatenated."""
        return "\n\n---\n\n".join([
            QuickReference.gamma_api(),
            QuickReference.clob_api(),
            QuickReference.order_flow(),
            QuickReference.auth_setup(),
            QuickReference.agent_architecture(),
            QuickReference.market_concepts(),
        ])
