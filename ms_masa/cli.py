"""
Ms-MASA CLI - Command-line interface for the Polymarket Agent Specialist.

Usage:
    python -m ms_masa status
    python -m ms_masa explain <topic>
    python -m ms_masa ref <card>
    python -m ms_masa scan [--tag TAG] [--limit N] [--sort FIELD]
    python -m ms_masa search <query>
    python -m ms_masa analyze <market_id>
    python -m ms_masa signals [--limit N]
    python -m ms_masa build <template> [--output FILE]
    python -m ms_masa scaffold <name> [--type TYPE]
    python -m ms_masa topics
    python -m ms_masa templates
"""

from __future__ import annotations

import argparse
import json
import sys

from ms_masa.agent import MsMasaAgent
from ms_masa.builder.agent_builder import AgentBuilder
from ms_masa.utils.formatters import Formatter


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="ms-masa",
        description="Ms-MASA: Polymarket Agent Specialist",
    )
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # status
    sub.add_parser("status", help="Check agent and API status")

    # explain
    p = sub.add_parser("explain", help="Look up a Polymarket topic")
    p.add_argument("topic", help="Topic name (use 'topics' to list)")

    # ref
    p = sub.add_parser("ref", help="Get a quick reference card")
    p.add_argument("card", nargs="?", default="all",
                    help="Card name: gamma_api, clob_api, order_flow, auth_setup, agent_architecture, market_concepts, all")

    # scan
    p = sub.add_parser("scan", help="Scan live markets")
    p.add_argument("--tag", help="Filter by tag")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--sort", default="volume", help="Sort by: volume, liquidity, certainty, uncertainty")
    p.add_argument("--min-volume", type=float, default=0)
    p.add_argument("--min-liquidity", type=float, default=0)

    # search
    p = sub.add_parser("search", help="Search markets by question")
    p.add_argument("query", help="Search query")
    p.add_argument("--limit", type=int, default=20)

    # analyze
    p = sub.add_parser("analyze", help="Deep analyze a market")
    p.add_argument("market_id", help="Market ID")

    # signals
    p = sub.add_parser("signals", help="Scan for market signals")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--spread", type=float, default=0.05)
    p.add_argument("--imbalance", type=float, default=0.3)

    # build
    p = sub.add_parser("build", help="Generate an agent from template")
    p.add_argument("template", help="Template: market_monitor, signal_scanner, data_collector, llm_analyst")
    p.add_argument("--output", help="Output filename")
    p.add_argument("--dir", default="./generated_agents", help="Output directory")

    # scaffold
    p = sub.add_parser("scaffold", help="Scaffold a complete agent project")
    p.add_argument("name", help="Project name")
    p.add_argument("--type", default="read_only_agent",
                    help="Agent type: read_only_agent, analytical_agent, trading_agent")
    p.add_argument("--dir", default="./generated_agents", help="Output directory")

    # topics
    sub.add_parser("topics", help="List knowledge base topics")

    # templates
    sub.add_parser("templates", help="List agent templates")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    agent = MsMasaAgent.from_env()

    if args.command == "status":
        print(json.dumps(agent.status(), indent=2))

    elif args.command == "explain":
        result = agent.explain(args.topic)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "ref":
        print(agent.ref(args.card))

    elif args.command == "scan":
        markets = agent.scan_markets(
            limit=args.limit,
            tag=args.tag,
            min_volume=args.min_volume,
            min_liquidity=args.min_liquidity,
            sort_by=args.sort,
        )
        if markets:
            print(Formatter.table(markets, ["question", "yes_price", "volume", "liquidity", "certainty"]))
        else:
            print("No markets found matching criteria.")

    elif args.command == "search":
        markets = agent.search_markets(args.query, limit=args.limit)
        if markets:
            print(Formatter.table(markets, ["question", "yes_price", "volume", "liquidity"]))
        else:
            print("No markets found.")

    elif args.command == "analyze":
        result = agent.analyze_market(args.market_id)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "signals":
        signals = agent.detect_signals(
            limit=args.limit,
            spread_threshold=args.spread,
            imbalance_threshold=args.imbalance,
        )
        if signals:
            for mid, sigs in signals.items():
                print(f"\nMarket: {mid}")
                print(Formatter.compact_signals(sigs))
        else:
            print("No signals detected.")

    elif args.command == "build":
        builder = AgentBuilder(output_dir=args.dir)
        code = builder.generate(args.template, output_file=args.output)
        print(f"Generated {args.template} agent in {args.dir}/")

    elif args.command == "scaffold":
        builder = AgentBuilder(output_dir=args.dir)
        files = builder.write_scaffold(args.name, agent_type=args.type)
        print(f"Scaffolded project '{args.name}':")
        for f in files:
            print(f"  {f}")

    elif args.command == "topics":
        from ms_masa.knowledge.polymarket_kb import PolymarketKB
        for t in PolymarketKB.topics():
            print(f"  {t}")

    elif args.command == "templates":
        from ms_masa.builder.templates import AgentTemplates
        for name, desc in AgentTemplates.list_templates().items():
            print(f"  {name}: {desc}")


if __name__ == "__main__":
    main()
