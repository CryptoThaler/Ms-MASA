# Ms-MASA Roadmap: From Agent Toolkit to Agentic Marketplace

## Current State (v0.1.0)

Ms-MASA is a Polymarket Agent Specialist with:
- **Knowledge Base** - Instant Polymarket platform knowledge (zero API calls)
- **API Clients** - Gamma (discovery) + CLOB (order books, trading)
- **Analysis Engine** - Market structure analysis, signal detection
- **Agent Builder** - 4 templates, project scaffolding
- **MCP Server** - 10 tools + 4 resources for Claude Desktop/Code
- **A2A Server** - Google Agent-to-Agent protocol endpoint
- **Skill Manifest** - 9 skills, 4 pricing tiers, multi-protocol export
- **Marketplace Hooks** - OLAS, NFT, and metered billing adapters
- **Framework Integrations** - LangChain, CrewAI, AutoGen, OpenAI
- **Fetch.ai uAgent** - Agentverse-compatible wrapper

---

## Three Strategic Directions

### Direction 1: MCP Skill Server (Ship Now)

**What:** Ms-MASA as a plug-and-play MCP server that any AI agent can discover.

**Why:** MCP is the de facto standard for tool integration. Claude Desktop has
50M+ users. Cursor, Windsurf, and dozens of IDE extensions support MCP.
One config line = instant distribution.

**How:**
```
pip install ms-masa
# Add to claude_desktop_config.json:
{"mcpServers": {"ms-masa": {"command": "python", "args": ["-m", "ms_masa.mcp_server"]}}}
```

**Revenue Model:** Freemium.
- Free tier: 5 knowledge skills (explain, reference, context, build, ecosystem)
- Metered tier: 4 API-backed skills ($X per 1000 calls)
- Premium tier: Custom agent generation, priority data

**Status:** READY. Both `mcp_server.py` (raw JSON-RPC) and `mcp_server_v2.py`
(FastMCP) are implemented and tested.

**Next Steps:**
1. Publish to PyPI (`pip install ms-masa`)
2. Submit to [MCP Server Registry](https://github.com/modelcontextprotocol/servers)
3. Add SSE transport for remote hosting
4. Build metering middleware for paid tiers

---

### Direction 2: Agent Marketplace (Near-Term)

**What:** Ms-MASA skills tradeable in agent-to-agent marketplaces.

**Why:** The agentic economy is emerging. Agents need to hire other agents'
skills. Ms-MASA is a specialized skill provider.

**Protocols (by readiness):**

| Protocol | Status | File | Next Step |
|----------|--------|------|-----------|
| **MCP** | Ready | `mcp_server.py` | PyPI + Registry |
| **Google A2A** | Ready | `a2a_server.py` | Host agent card at well-known URL |
| **LangChain** | Ready | `integrations.py` | Publish as LangChain Community tool |
| **CrewAI** | Ready | `integrations.py` | Add to CrewAI tool catalog |
| **OpenAI** | Ready | `integrations.py` | GPT Actions / function definitions |
| **OLAS/Autonolas** | Descriptor ready | `marketplace.py` | Deploy to Gnosis Chain |
| **Fetch.ai** | Agent ready | `uagent_wrapper.py` | Register on Agentverse |
| **Morpheus** | Conceptual | `marketplace.py` | MOR20 subnet deployment |

**Revenue Model:** Per-call metering + subscription tiers.
- `MarketplaceAdapter` tracks usage, enforces rate limits
- Billing data exportable for any payment system

**Next Steps:**
1. Deploy A2A server to a public endpoint
2. Register on Agentverse marketplace
3. Build REST API wrapper for `MarketplaceAdapter`
4. Add Stripe/crypto payment integration

---

### Direction 3: On-Chain Skill Economy (Medium-Term)

**What:** Ms-MASA agent configurations as tradeable on-chain assets.

**Why:** Agent skills have economic value. On-chain registration provides
trustless discovery, composability, and revenue sharing.

**Three On-Chain Patterns:**

#### Pattern A: OLAS Autonomous Service
```
Register as OLAS service on Gnosis Chain
├── Component Registry  (9 skill components)
├── Agent Registry      (Ms-MASA agent definition)
├── Service Registry    (Composable service with staking)
└── Revenue             (OLAS staking rewards + usage fees)
```
- Operators stake OLAS to run Ms-MASA instances
- Service owner earns from staking emissions + fees
- File: `marketplace.py` → `OnChainServiceDescriptor`

#### Pattern B: Skill NFTs (ERC-721)
```
Mint agent configurations as tradeable NFTs
├── Market Sentinel    (Common)  - Monitor + Signals
├── Alpha Hunter       (Rare)    - Advanced analysis + correlation
├── Full Stack         (Legendary) - All capabilities
└── Custom configs     (User-generated via builder)
```
- Encode skill combinations + parameters in NFT metadata
- Trade on OpenSea / Blur / any NFT marketplace
- "Equip" NFTs in agent frameworks to gain capabilities
- Royalties on secondary sales
- File: `marketplace.py` → `SkillNFTMetadata`, `SKILL_NFT_TEMPLATES`

#### Pattern C: Morpheus Builder Subnet
```
Deploy as MOR20 subnet on Base
├── Ms-MASA skill token
├── MOR holder staking → access to Polymarket intelligence
├── Builder rewards from MOR emissions
└── Compute marketplace for API-backed queries
```

**Next Steps:**
1. Write Solidity contract for Skill NFT minting
2. Deploy OLAS service components via `autonomy` CLI
3. Explore Morpheus Builder registration

---

## Implementation Priorities

### Phase 1: Distribution (Now)
- [ ] Publish `ms-masa` to PyPI
- [ ] Submit MCP server to the MCP Server Registry
- [ ] Deploy A2A agent card to a public URL
- [ ] Register Fetch.ai uAgent on Agentverse
- [ ] Publish LangChain community tool

### Phase 2: Monetization (Next)
- [ ] Build REST API around MarketplaceAdapter (FastAPI)
- [ ] Add Stripe metered billing for API-backed skills
- [ ] Deploy OLAS service components on Gnosis Chain
- [ ] Add WebSocket streaming support to MCP server

### Phase 3: On-Chain Economy (Future)
- [ ] Deploy Skill NFT contract on Polygon
- [ ] Mint initial skill configurations (3 tiers)
- [ ] Build NFT-gated agent loading (equip NFT → gain skills)
- [ ] Explore Morpheus MOR20 subnet deployment
- [ ] Cross-chain skill discovery (Polygon ↔ Gnosis ↔ Base)

### Phase 4: Autonomous Agent Network (Vision)
- [ ] Multi-agent orchestration (Ms-MASA as a worker in agent swarms)
- [ ] Self-improving knowledge base (agents update KB from market activity)
- [ ] Cross-protocol skill composition (MCP + A2A + OLAS)
- [ ] Decentralized skill reputation (on-chain track record)

---

## Architecture: How It All Fits Together

```
                    ┌─────────────────────────────┐
                    │     DISCOVERY LAYER          │
                    ├─────────────────────────────┤
                    │  MCP Registry   (tool list)  │
                    │  A2A Agent Card (/.well-known)│
                    │  OLAS Registry  (on-chain)   │
                    │  Agentverse     (Fetch.ai)   │
                    │  PyPI Package   (pip install) │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │     PROTOCOL LAYER           │
                    ├─────────────────────────────┤
                    │  MCP Server    (stdio/HTTP)   │
                    │  A2A Server    (JSON-RPC/HTTP) │
                    │  uAgent        (Almanac)      │
                    │  REST API      (FastAPI)       │
                    │  Python Import (direct)        │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │     METERING LAYER           │
                    ├─────────────────────────────┤
                    │  MarketplaceAdapter           │
                    │  - Usage tracking             │
                    │  - Rate limiting              │
                    │  - Billing (Stripe/crypto)    │
                    │  - Access control             │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │     SKILL LAYER              │
                    ├─────────────────────────────┤
                    │  Knowledge (5 free skills)    │
                    │  Market Data (4 metered)      │
                    │  Analysis + Signals           │
                    │  Agent Builder                │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │     DATA LAYER               │
                    ├─────────────────────────────┤
                    │  Polymarket KB  (compiled)    │
                    │  Gamma API     (discovery)    │
                    │  CLOB API      (order books)  │
                    │  WebSocket     (streaming)    │
                    └─────────────────────────────┘
```

---

## File Map

| File | Purpose |
|------|---------|
| `ms_masa/mcp_server.py` | MCP v1 (raw JSON-RPC, no deps) |
| `ms_masa/mcp_server_v2.py` | MCP v2 (FastMCP, HTTP/SSE) |
| `ms_masa/a2a_server.py` | Google A2A protocol server |
| `ms_masa/uagent_wrapper.py` | Fetch.ai uAgent wrapper |
| `ms_masa/skill_manifest.py` | Multi-protocol skill definitions |
| `ms_masa/marketplace.py` | On-chain + metering + NFT hooks |
| `ms_masa/integrations.py` | LangChain/CrewAI/AutoGen/OpenAI |
| `plugin/` | Claude Agent SDK plugin package |
| `mcp.json` | Claude Code MCP config |

---

## Quick Install Reference

```bash
# Direct Python
pip install ms-masa
python -c "from ms_masa import MsMasaAgent; print(MsMasaAgent().explain('platform'))"

# MCP (Claude Desktop/Code)
# Add to config: {"mcpServers": {"ms-masa": {"command": "python", "args": ["-m", "ms_masa.mcp_server"]}}}

# A2A Server
python -m ms_masa.a2a_server --port 9999

# Fetch.ai Agent
pip install uagents ms-masa
python -m ms_masa.uagent_wrapper

# LangChain
from ms_masa.integrations import langchain_tools
tools = langchain_tools()

# CrewAI
from ms_masa.integrations import crewai_tools

# CLI
ms-masa scan --tag politics --limit 10
ms-masa marketplace advertise
ms-masa install-guide
```
