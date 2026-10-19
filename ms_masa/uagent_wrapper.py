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
import os
import secrets
import sys
from pathlib import Path

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


SEED_ENV = "MS_MASA_UAGENT_SEED"
DEFAULT_SEED_PATH = Path.home() / ".ms_masa" / "uagent_seed"
MIN_SEED_LENGTH = 32


def resolve_seed(seed: str | None = None, seed_path: Path = DEFAULT_SEED_PATH) -> str:
    """
    Resolve the agent seed: explicit arg, then $MS_MASA_UAGENT_SEED, then a
    per-install random seed persisted (mode 0600) at seed_path.

    The seed deterministically derives the agent's on-chain identity, so it
    must be secret and unique per deployment.
    """
    seed = seed or os.getenv(SEED_ENV)
    if seed:
        if len(seed) < MIN_SEED_LENGTH:
            raise SystemExit(f"uAgent seed must be at least {MIN_SEED_LENGTH} characters")
        return seed

    if seed_path.exists():
        return seed_path.read_text().strip()

    seed_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    seed = secrets.token_hex(32)
    fd = os.open(seed_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(seed)
    print(f"Generated new uAgent seed at {seed_path}", file=sys.stderr)
    return seed


def create_agent(seed: str | None = None, port: int = 8001):
    """
    Create and configure the Ms-MASA uAgent.

    Returns the configured agent ready to run.
    Requires: pip install uagents
    """
    seed = resolve_seed(seed)
    try:
        from uagents import Agent, Context, Model
    except ImportError:
        print(
            "Fetch.ai uAgents SDK required: pip install uagents",
            file=sys.stderr,
        )
        sys.exit(1)

    from ms_masa.security import public_error

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
                skill="explain", data=json.dumps({"error": public_error(e, "uagent explain")}), success=False,
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
                skill="markets", data=json.dumps({"error": public_error(e, "uagent markets")}), success=False,
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
                skill="analyze", data=json.dumps({"error": public_error(e, "uagent analyze")}), success=False,
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
                skill="signals", data=json.dumps({"error": public_error(e, "uagent signals")}), success=False,
            ))

    return agent


# ── Entry Point ────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Ms-MASA Fetch.ai uAgent")
    parser.add_argument(
        "--seed", default=None,
        help=f"Agent seed (prefer ${SEED_ENV}; defaults to a generated seed in {DEFAULT_SEED_PATH})",
    )
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
