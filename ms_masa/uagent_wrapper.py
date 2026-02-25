"""
Ms-MASA Fetch.ai uAgent Wrapper.

Wraps Ms-MASA as a Fetch.ai micro-agent that auto-registers on the
Almanac smart contract, making it discoverable in the Agentverse marketplace.

Install:
    pip install uagents ms-masa

Run:
    python -m ms_masa.uagent_wrapper

The agent registers on Almanac and responds to MarketQuery, AnalysisQuery,
SignalQuery, and KnowledgeQuery messages from other uAgents.

Protocol: https://docs.fetch.ai/uagents/
"""

from __future__ import annotations

import json
import sys

# ── Message Models (can be used without uagents installed) ─────────────

# These define the A2A message schema for the Fetch.ai protocol.
# Other uAgents import these models to communicate with Ms-MASA.

MESSAGE_SCHEMAS = {
    "KnowledgeQuery": {
        "topic": "str - Knowledge topic (platform, apis, clob, etc.)",
    },
    "MarketQuery": {
        "query": "str - Search text or empty for scan",
        "limit": "int - Max results (default: 10)",
        "tag": "str | None - Category filter",
        "sort_by": "str - Sort field (default: volume)",
    },
    "AnalysisQuery": {
        "market_id": "str - Polymarket market ID",
    },
    "SignalQuery": {
        "limit": "int - Markets to scan (default: 30)",
        "spread_threshold": "float - Min spread (default: 0.05)",
    },
    "MasaResponse": {
        "skill": "str - Skill that handled the query",
        "data": "str - JSON-encoded result",
        "success": "bool - Whether the query succeeded",
    },
}


def create_agent(seed: str = "ms-masa-polymarket-agent", port: int = 8001):
    """
    Create and configure the Ms-MASA uAgent.

    Returns the configured agent ready to run.
    Requires: pip install uagents
    """
    try:
        from uagents import Agent, Context, Model
    except ImportError:
        print(
            "Fetch.ai uAgents SDK required: pip install uagents",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Define message models ──────────────────────────────────────

    class KnowledgeQuery(Model):
        topic: str = "platform"

    class MarketQuery(Model):
        query: str = ""
        limit: int = 10
        tag: str = ""
        sort_by: str = "volume"

    class AnalysisQuery(Model):
        market_id: str

    class SignalQuery(Model):
        limit: int = 30
        spread_threshold: float = 0.05

    class MasaResponse(Model):
        skill: str
        data: str
        success: bool = True

    # ── Create agent ───────────────────────────────────────────────

    agent = Agent(
        name="ms-masa-polymarket",
        seed=seed,
        port=port,
        endpoint=[f"http://localhost:{port}/submit"],
    )

    # ── Lazy Ms-MASA instance ─────────────────────────────────────

    _masa = {}

    def get_masa():
        if "agent" not in _masa:
            from ms_masa.agent import MsMasaAgent
            _masa["agent"] = MsMasaAgent.from_env()
        return _masa["agent"]

    # ── Handlers ──────────────────────────────────────────────────

    @agent.on_event("startup")
    async def startup(ctx: Context):
        ctx.logger.info(f"Ms-MASA uAgent started: {ctx.agent.address}")
        ctx.logger.info(f"Skills: knowledge, scan, search, analyze, signals")

    @agent.on_message(model=KnowledgeQuery)
    async def handle_knowledge(ctx: Context, sender: str, msg: KnowledgeQuery):
        ctx.logger.info(f"Knowledge query from {sender}: {msg.topic}")
        try:
            result = get_masa().explain(msg.topic)
            await ctx.send(sender, MasaResponse(
                skill="explain",
                data=json.dumps(result, default=str),
                success=True,
            ))
        except Exception as e:
            await ctx.send(sender, MasaResponse(
                skill="explain", data=json.dumps({"error": str(e)}), success=False,
            ))

    @agent.on_message(model=MarketQuery)
    async def handle_market(ctx: Context, sender: str, msg: MarketQuery):
        ctx.logger.info(f"Market query from {sender}: query={msg.query}, tag={msg.tag}")
        try:
            masa = get_masa()
            if msg.query:
                result = masa.search_markets(msg.query, limit=msg.limit)
            else:
                result = masa.scan_markets(
                    limit=msg.limit,
                    tag=msg.tag if msg.tag else None,
                    sort_by=msg.sort_by,
                )
            await ctx.send(sender, MasaResponse(
                skill="markets",
                data=json.dumps(result, default=str),
                success=True,
            ))
        except Exception as e:
            await ctx.send(sender, MasaResponse(
                skill="markets", data=json.dumps({"error": str(e)}), success=False,
            ))

    @agent.on_message(model=AnalysisQuery)
    async def handle_analysis(ctx: Context, sender: str, msg: AnalysisQuery):
        ctx.logger.info(f"Analysis query from {sender}: {msg.market_id}")
        try:
            result = get_masa().analyze_market(msg.market_id)
            await ctx.send(sender, MasaResponse(
                skill="analyze",
                data=json.dumps(result, default=str),
                success=True,
            ))
        except Exception as e:
            await ctx.send(sender, MasaResponse(
                skill="analyze", data=json.dumps({"error": str(e)}), success=False,
            ))

    @agent.on_message(model=SignalQuery)
    async def handle_signals(ctx: Context, sender: str, msg: SignalQuery):
        ctx.logger.info(f"Signal query from {sender}: limit={msg.limit}")
        try:
            result = get_masa().detect_signals(
                limit=msg.limit, spread_threshold=msg.spread_threshold,
            )
            await ctx.send(sender, MasaResponse(
                skill="signals",
                data=json.dumps(result, default=str),
                success=True,
            ))
        except Exception as e:
            await ctx.send(sender, MasaResponse(
                skill="signals", data=json.dumps({"error": str(e)}), success=False,
            ))

    return agent


# ── Entry Point ────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Ms-MASA Fetch.ai uAgent")
    parser.add_argument("--seed", default="ms-masa-polymarket-agent", help="Agent seed phrase")
    parser.add_argument("--port", type=int, default=8001, help="Agent port")
    parser.add_argument("--schemas", action="store_true", help="Print message schemas and exit")
    args = parser.parse_args()

    if args.schemas:
        print(json.dumps(MESSAGE_SCHEMAS, indent=2))
        return

    agent = create_agent(seed=args.seed, port=args.port)
    agent.run()


if __name__ == "__main__":
    main()
