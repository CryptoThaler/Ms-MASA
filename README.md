# Ms-MASA: Polymarket Agent Specialist

A low-token, high-performance agent framework for building autonomous systems on the Polymarket prediction market platform.

**NOT for financial advice or trading.** Focused on agent architecture, API integration, and understanding the Polymarket ecosystem's potential for agentic systems.

## Architecture

```
ms_masa/
  agent.py              # Core agent - orchestrates all modules
  models.py             # Data models (Market, Event, OrderBook, Trade, signals)
  config.py             # Configuration management
  prompts.py            # LLM system prompts for different agent modes
  cli.py                # Command-line interface
  api/
    gamma.py            # Gamma API client (market discovery)
    clob.py             # CLOB API client (order books, prices)
    data_pipe.py        # Data pipeline (aggregates Gamma + CLOB)
  analysis/
    market_analyzer.py  # Market structure analysis
    signals.py          # Signal detection engine
  knowledge/
    polymarket_kb.py    # Compressed knowledge base (zero API calls)
    reference.py        # Quick reference cards for operations
    ecosystem.py        # Full ecosystem reference
  builder/
    agent_builder.py    # Agent generation toolkit
    templates.py        # Ready-to-use agent templates
  utils/
    formatters.py       # Token-efficient output formatting
```

## Quick Start

```python
from ms_masa import MsMasaAgent

agent = MsMasaAgent()

# Instant knowledge lookup (no API calls)
agent.explain("platform")      # Platform architecture
agent.explain("apis")          # All API endpoints
agent.explain("contracts")     # Smart contract addresses
agent.explain("patterns")      # Agent building patterns

# Quick reference cards
agent.ref("clob_api")          # CLOB API reference
agent.ref("gamma_api")         # Gamma API reference
agent.ref("order_flow")        # Order flow reference
agent.ref("auth_setup")        # Authentication setup
agent.ref("agent_architecture") # Agent architecture reference

# Compact LLM context (minimal tokens)
context = agent.get_agent_context("analytical_agent")
```

## Live Market Data

```python
# Scan markets (requires internet)
markets = agent.scan_markets(limit=20, sort_by="volume")
markets = agent.scan_markets(tag="politics", min_volume=10000)
results = agent.search_markets("election")

# Deep analysis
analysis = agent.analyze_market("market-id")
book = agent.get_order_book("token-id")
event = agent.get_event("event-id")

# Signal detection
signals = agent.detect_signals(limit=50, spread_threshold=0.05)
```

## Agent Builder

```python
from ms_masa.builder import AgentBuilder

builder = AgentBuilder()

# List templates
builder.list_templates()
# -> market_monitor, signal_scanner, data_collector, llm_analyst

# Generate agent code
builder.generate("market_monitor")
builder.generate("signal_scanner")
builder.generate("llm_analyst")

# Scaffold complete project
builder.write_scaffold("my_agent", agent_type="analytical_agent")
```

## CLI

```bash
python -m ms_masa status                        # Agent + API health
python -m ms_masa explain platform              # Knowledge lookup
python -m ms_masa ref clob_api                  # Quick reference
python -m ms_masa scan --limit 20 --sort volume # Scan markets
python -m ms_masa search "bitcoin"              # Search markets
python -m ms_masa analyze <market_id>           # Deep analysis
python -m ms_masa signals --limit 50            # Signal scan
python -m ms_masa build market_monitor          # Generate agent
python -m ms_masa scaffold my_agent             # Scaffold project
python -m ms_masa topics                        # List KB topics
python -m ms_masa templates                     # List templates
```

## Knowledge Base Topics

| Topic | Content |
|-------|---------|
| `platform` | Architecture, chain, token, settlement |
| `apis` | Gamma + CLOB endpoint reference |
| `gamma` | Market discovery API details |
| `clob` | Order book + trading API details |
| `orders` | GTC, FOK, GTD, FAK order types |
| `auth` | Signature types, credential flow, approvals |
| `sdks` | Python, TypeScript, Rust SDK reference |
| `contracts` | CTF Exchange, NegRisk, Conditional Tokens |
| `market_structure` | Event > Market > Outcome > Token hierarchy |
| `patterns` | Read-only, Analytical, Trading agent patterns |

## Polymarket Ecosystem Coverage

Built from analysis of the complete `github.com/Polymarket` organization:

- **py-clob-client** - Python CLOB SDK (orders, books, prices)
- **clob-client** - TypeScript CLOB SDK
- **rs-clob-client** - Rust CLOB SDK with type-safe state machine
- **agents** - AI agent framework (LLM + RAG + trading)
- **ctf-exchange** - Core exchange smart contracts (Solidity/Foundry)
- **uma-ctf-adapter** - UMA oracle resolution adapter
- **neg-risk-ctf-adapter** - Multi-outcome market adapter
- **polymarket-subgraph** - GraphQL on-chain data indexing

## Configuration

```bash
cp .env.example .env
# Edit .env with your credentials (optional for read-only mode)
```

Environment variables:
- `POLYGON_WALLET_PRIVATE_KEY` - For authenticated CLOB operations
- `OPENAI_API_KEY` - For LLM-powered analysis
- `POLYMARKET_CLOB_URL` - Custom CLOB endpoint
- `POLYMARKET_GAMMA_URL` - Custom Gamma endpoint

## Install

```bash
pip install -r requirements.txt
# or
pip install -e .
```

## License

MIT
