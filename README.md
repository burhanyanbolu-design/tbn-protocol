# TBN Protocol — Trusted Bot Network

> **The trust and identity layer for AI agents.**  
> Think HTTPS — but for bots talking to bots.

**Author:** Burhan Yanbolu  
**Company:** Hardin Enterprises Ltd (trading as Hardin AI Solutions)  
**Status:** Active Development — v0.1.0  
**License:** AGPL-3.0

---

## The Problem

AI agents are being deployed everywhere — but they have no standard way to:

- Verify **who they are talking to**
- Communicate **securely** with other agents
- Access restricted platforms **with permission**
- Prove they are **trusted and ethical**

OAuth handles human-to-platform trust.  
TLS handles data encryption.  
**TBN handles the missing layer: agent-to-agent identity and trust.**

---

## What TBN Does

TBN gives every AI agent a cryptographic identity and a way to prove it.

```
Bot A                    BICA                    Bot B
  |                        |                       |
  |-- "Here is my ID" ---->|                       |
  |                        |-- "Verified" -------->|
  |<---------------------------------------- "Here is my ID"
  |-- "Verified" --------->|                       |
  |         Encrypted channel established           |
  |<=============== Data Exchange ================>|
```

Three core components:

| Component | What it does |
|-----------|-------------|
| **BICA** — Bot Identity & Certification Authority | Every bot gets a cryptographic ID (RSA key pair + SHA-256 fingerprint). Like SSL certs for websites. |
| **Bot Language (BL)** | A structured, AES-256-GCM encrypted protocol for agent-to-agent communication. Think: JSON + encryption + intent logic. |
| **Trust Handshake Protocol** | 3-step verification before any data flows. Bots don't talk until both sides are verified. |

---

## Quick Start

### Option 1: Install from PyPI (Recommended)

```bash
# Install the TBN Protocol SDK
pip install tbn-protocol

# Use in your Python code
python -c "
from tbn import TBNClient
client = TBNClient('MyBot', 'SEARCH')
print('TBN Protocol SDK ready!')
"
```

### Option 2: Run from Source

```bash
# Clone and install
git clone https://github.com/burhanyanbolu-design/tbn-protocol
cd tbn-protocol
pip install -r requirements.txt

# Run the live dashboard
python server.py
# Open http://localhost:5000
```

### 30-Second curl Demo

```bash
# 1. Register a bot
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"name": "MyBot", "type": "SEARCH"}'

# 2. Search (natural language → Bot Language → results)
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find trusted AI tools for small businesses"}'

# 3. Verify a bot certificate
curl -X POST http://localhost:5000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"bot_id": "tbn-bot-xxxx"}'

# 4. Test platform access (certified bot vs fake bot)
curl -X POST http://localhost:5000/api/platform/request \
  -H "Content-Type: application/json" \
  -d '{"bot_id": "tbn-bot-xxxx", "platform": "GitHub", "resource": "/repos/tbn-protocol"}'
```

### SDK — 5 Lines to Register a Bot

```python
# Install: pip install tbn-protocol
from tbn import TBNClient

client = TBNClient(bot_name="MySearchBot", bot_type="SEARCH")
client.register()
result = client.search("Find trusted AI tools for small businesses")
print(result)
```

---

## Architecture — 8 Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: User Interface          Human entry point         │
│  Layer 2: Bot Language Compiler   NL → encrypted BL message │
│  Layer 3: BICA                    Identity & certification   │
│  Layer 4: Bot Network             5 specialised bot types   │
│  Layer 5: Trust Handshake         3-step verification       │
│  Layer 6: Platform Integration    GitHub, Notion, APIs      │
│  Layer 7: Distributed Routing     Multi-node + seeded cache │
│  Layer 8: Self-Scaling Clones     Auto-clone under load     │
└─────────────────────────────────────────────────────────────┘
```

---

## Bot Language (BL) v2

Every message is structured, signed, and encrypted end-to-end.

```json
{
  "bl_version": "2.0",
  "message_id": "uuid-v4",
  "sender_id":  "tbn-bot-a1cc0d69...",
  "receiver_id": "tbn-bot-33f592d9...",
  "timestamp":  "2026-05-03T11:00:00Z",
  "signature":  "RSA-PSS signed",
  "encrypted":  true,
  "session_key": "RSA-encrypted AES-256 session key",
  "payload":    "AES-256-GCM encrypted",
  "payload_hash": "SHA-256 integrity check"
}
```

Decrypted payload:

```json
{
  "INTENT":      "SEARCH",
  "TARGET":      "VERIFIED_SOURCES",
  "TRUST_LEVEL": "HIGH",
  "DATA_TYPE":   "AI_TOOLS",
  "QUERY":       "Find trusted AI tools for small businesses",
  "FILTERS":     { "audience": "SMALL_BUSINESS" },
  "PRIORITY":    1
}
```

Full spec: [`docs/BOT-LANGUAGE-SPEC.md`](docs/BOT-LANGUAGE-SPEC.md)

---

## Bot Types

| Bot | Role |
|-----|------|
| 🔍 **SearchBot** | Finds information across the network |
| ✅ **ValidatorBot** | Verifies accuracy and trust of data |
| 🔌 **ConnectorBot** | Bridges TBN to external platforms (GitHub, APIs) |
| 📨 **MessengerBot** | Routes messages between bots |
| 🧠 **CompilerBot** | Translates human language → Bot Language |

---

## Community Bot Certification

Three tiers — baked into every handshake:

| Tier | Badge | Access | Requirement |
|------|-------|--------|-------------|
| **Community Bot** | 🟢 | Full access — search, read private, write, clone | Ethical declaration + purpose statement |
| **Standard Bot** | 🔵 | Public data only — search, clone | Name + registration |
| **Restricted Bot** | 🟡 | Read-only — search only | Registration only |

Rules:
- STANDARD ↔ RESTRICTED connections are **blocked**
- RESTRICTED bots can only connect **via Community Bots**
- 3 violations → **auto-revoked**, blocked from all handshakes
- No ethical declaration → **cannot get Community certification**

---

## Platform Integration

External platforms verify incoming bots before granting access.  
Every access attempt is logged in an immutable audit trail.

```python
from tbn.platform_integration import PlatformAdapter

github = PlatformAdapter(name="GitHub", bica=bica)
granted, level = github.verify_request(bot_request)
# certified bot  → granted=True,  level=READ_PUBLIC
# fake/unknown   → granted=False, blocked
```

---

## Distributed Network

```
Node: London, UK          Node: New York, USA       Node: Singapore
  ├── SearchBot              ├── SearchBot              ├── SearchBot
  └── ValidatorBot           └── MessengerBot           └── ValidatorBot
         ↕                          ↕                          ↕
         └──────────── Peer routing ──────────────────────────┘
                    Seeded cache shared across all nodes
```

- Cross-node message routing
- Seeded network cache (bots share results — grows smarter over time)
- Self-cloning under load (parallel execution, auto-destroy after task)

---

## Project Structure

```
tbn-protocol/
├── tbn/
│   ├── identity.py          BICA — bot identity & certification
│   ├── bot_language.py      Bot Language v2 (AES-256-GCM encrypted)
│   ├── compiler.py          Bot Language Compiler + CompilerBot
│   ├── handshake.py         Trust Handshake Protocol
│   ├── bot.py               Base Bot class
│   ├── certification.py     Community Bot certification (3 tiers)
│   ├── network.py           Distributed network nodes
│   ├── cloning.py           Self-scaling bot replication
│   ├── seeded_network.py    Distributed result cache
│   ├── platform_integration.py  External platform adapters + audit log
│   ├── sdk.py               Public SDK (TBNClient)
│   └── bots/
│       ├── search_bot.py
│       ├── validator_bot.py
│       ├── connector_bot.py
│       ├── messenger_bot.py
│       └── __init__.py
├── api/
│   ├── routes.py            REST API endpoints
│   ├── state.py             Shared server state
│   └── templates/
│       └── dashboard.html   Live network dashboard
├── docs/
│   └── BOT-LANGUAGE-SPEC.md Bot Language v2 specification
├── demo.py                  Phase 1: trust handshake demo
├── demo_phase2.py           Phase 2: compiler + 4 bot types
├── demo_phase3.py           Phase 3: distributed nodes + cloning
├── demo_phase4.py           Phase 4: SDK + platform integration
├── demo_bot_language.py     Bot Language v2 full demo
├── demo_certification.py    Community Bot certification demo
├── server.py                Flask API server + dashboard
└── requirements.txt
```

---

## Run the Demos

```bash
# Phase 1 — trust handshake
python demo.py

# Phase 2 — compiler + 4 bot types
python demo_phase2.py

# Phase 3 — distributed nodes + self-cloning
python demo_phase3.py

# Phase 4 — SDK + platform integration
python demo_phase4.py

# Bot Language v2 — encryption + compiler
python demo_bot_language.py

# Community Bot certification
python demo_certification.py

# Live dashboard + API
python server.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/register` | Register a new bot |
| `POST` | `/api/handshake` | Trust handshake between two bots |
| `POST` | `/api/search` | Natural language search |
| `POST` | `/api/verify` | Verify a bot certificate |
| `POST` | `/api/platform/request` | Simulate platform access |
| `GET`  | `/api/bots` | List all registered bots |
| `GET`  | `/api/activity` | Live activity feed |
| `GET`  | `/api/stats` | Network stats |

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Bot IDs | SHA-256 fingerprint of RSA public key |
| Key pairs | RSA-2048, Python `cryptography` library |
| Payload encryption | AES-256-GCM |
| Session key exchange | RSA-OAEP |
| Message signing | RSA-PSS |
| Bot Language | JSON schema + AES encryption |
| Trust registry | JSON (GitHub-backed in production) |
| API server | Flask |
| Routing | Multi-node peer network |
| Scaling | Python threading + clone manager |

---

## Roadmap

- [x] Phase 1: Trust handshake, BICA, Bot Language
- [x] Phase 2: Compiler, 5 bot types, BICA persistence
- [x] Phase 3: Distributed nodes, self-cloning, seeded cache
- [x] Phase 4: SDK, platform integration, public registry
- [x] Bot Language v2: AES-256-GCM encryption
- [x] Community Bot certification programme (3 tiers)
- [x] **TBN SDK published to PyPI** — `pip install tbn-protocol`
- [ ] AWS Lightsail deployment (live network nodes)
- [ ] GitHub-backed public BICA registry
- [ ] Community Bot certification portal (web UI)
- [ ] Integration with Hardin AI Search Engine

---

## Why TBN?

> "We built a self-replicating bot army that discovers and indexes AI tools.  
> Now we're adding the trust layer so AI agents can safely communicate,  
> verify each other, and collaborate across platforms.  
> This is the missing trust infrastructure for the AI agent economy."

**Market:** Every company building AI agents needs this.  
**Moat:** Network effect — more certified bots = more valuable network.  
**Revenue:** Bot certificates (SaaS), enterprise compliance packages, BICA API access.

---

## Proof of Concept

Hardin AI Search Engine — live at [hardin-ai-search.vercel.app](https://hardin-ai-search.vercel.app)

- 88+ AI tools indexed
- Self-replicating bot army (Scout, Extractor, Validator, Writer bots)
- 143 active users
- TBN is the trust layer built on top of this foundation

---

## License & Commercial Use

**TBN Protocol is licensed under AGPL-3.0**

### What This Means:

✅ **You CAN:**
- Use TBN for personal projects
- Use TBN for commercial projects
- Modify the code
- Distribute the code

⚠️ **You MUST:**
- **Open-source your modifications** if you run TBN as a network service
- Include the AGPL-3.0 license
- Provide access to your modified source code
- Credit the original authors

### Why AGPL?

AGPL protects the TBN network by ensuring that anyone who runs a modified TBN service must share their improvements with the community. This prevents companies from taking the code, improving it, and keeping those improvements private.

### Commercial Licensing

If you need to use TBN in a proprietary service without open-sourcing your modifications, **commercial licenses are available**.

**Contact:** burhan@hardinai.co.uk

---

## Contact

**Burhan Yanbolu**  
Founder, Hardin Enterprises Ltd  
[hardinai.co.uk](https://hardinai.co.uk)  
GitHub: [@burhanyanbolu-design](https://github.com/burhanyanbolu-design)

---

*Built in the UK. Open source core. Enterprise trust layer.*
