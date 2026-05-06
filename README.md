# TBN Protocol — Trusted Bot Network

> **The trust and identity layer for AI agents.**  
> Think HTTPS — but for bots talking to bots.

**Author:** Burhan Yanbolu  
**Company:** Hardin Enterprises Ltd (trading as Hardin AI Solutions)  
**Status:** Live — v0.1.0  
**License:** AGPL-3.0

[![PyPI](https://img.shields.io/pypi/v/tbn-protocol?color=blue&label=PyPI)](https://pypi.org/project/tbn-protocol/)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-tbn.hardinai.co.uk-green)](https://tbn.hardinai.co.uk)
[![BICA Registry](https://img.shields.io/badge/BICA%20Registry-GitHub-orange)](https://github.com/burhanyanbolu-design/tbn-bica-registry)

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
| **Bot Language (BL)** | A structured, AES-256-GCM encrypted protocol for agent-to-agent communication. |
| **Trust Handshake Protocol** | 3-step verification before any data flows. Bots don't talk until both sides are verified. |

---

## 🏢 Open Protocol, Centralized Network

**TBN Protocol is open source. TBN Network is centralized.**

Like Docker (open) + Docker Hub (centralized), or Git (open) + GitHub (centralized):

### What's Open Source:
- ✅ **TBN Protocol** — Specification and implementation
- ✅ **Client SDK** — `pip install tbn-protocol`
- ✅ **Bot Language** — Encrypted communication protocol
- ✅ **Documentation** — Full technical specs

### What's Centralized:
- 🔒 **The Registry** — Hosted at [tbn.hardinai.co.uk](https://tbn.hardinai.co.uk)
- 🔒 **Bot Certification** — Only we can issue trusted certificates
- 🔒 **Network Trust** — Companies trust OUR certification authority
- 🔒 **Enterprise Features** — Analytics, SLAs, compliance tools

### Why Centralized?

**Trust requires a single source of truth.**

- **Network Effect** — All companies and bots in one place
- **Trust** — "TBN-certified" means something because we control it
- **Reliability** — Enterprise-grade infrastructure, 99.9% uptime
- **Security** — Centralized monitoring, compliance, and enforcement

### Can I Self-Host?

Yes, for **development and testing**. But for production:

- ❌ Your bots won't be recognized by companies
- ❌ Companies won't trust your certifications
- ❌ You won't have access to the bot ecosystem
- ❌ No network effect, no value

**For production, connect to the official TBN Network.**

---

## Live Network

| URL | Description |
|-----|-------------|
| [tbn.hardinai.co.uk](https://tbn.hardinai.co.uk) | Live network dashboard |
| [tbn.hardinai.co.uk/register](https://tbn.hardinai.co.uk/register) | Register a bot (web UI) |
| [tbn.hardinai.co.uk/certification/portal](https://tbn.hardinai.co.uk/certification/portal) | Community Bot Certification Portal |
| [tbn.hardinai.co.uk/admin/violations](https://tbn.hardinai.co.uk/admin/violations) | Violations Dashboard |
| [github.com/burhanyanbolu-design/tbn-bica-registry](https://github.com/burhanyanbolu-design/tbn-bica-registry) | Public BICA Registry (GitHub-backed) |

---

## Quick Start

### Option 1: Install from PyPI (Recommended)

```bash
pip install tbn-protocol
```

```python
from tbn import TBNClient

client = TBNClient(bot_name="MyBot", bot_type="SEARCH")
client.register()
result = client.search("Find trusted AI tools for small businesses")
print(result)
```

### Option 2: Run from Source

```bash
git clone https://github.com/burhanyanbolu-design/tbn-protocol
cd tbn-protocol
pip install -r requirements.txt
python server.py
# Open http://localhost:5000
```

### 30-Second curl Demo

```bash
# 1. Register a bot
curl -X POST https://tbn.hardinai.co.uk/api/register \
  -H "Content-Type: application/json" \
  -d '{"name": "MyBot", "type": "SEARCH"}'

# 2. Search (natural language → Bot Language → results)
curl -X POST https://tbn.hardinai.co.uk/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find trusted AI tools for small businesses"}'

# 3. Verify a bot certificate
curl -X POST https://tbn.hardinai.co.uk/api/verify \
  -H "Content-Type: application/json" \
  -d '{"bot_id": "tbn-bot-xxxx"}'

# 4. Apply for Community certification
curl -X POST https://tbn.hardinai.co.uk/certification/certify \
  -H "Content-Type: application/json" \
  -d '{"bot_id": "tbn-bot-xxxx", "level": "COMMUNITY", "purpose": "AI tool discovery", "ethical_declaration": true}'
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

## Community Bot Certification

Three tiers — baked into every handshake:

| Tier | Badge | Access | Requirement |
|------|-------|--------|-------------|
| **Community** | 🟢 | Full access — read private, write, clone | Ethical declaration + purpose statement |
| **Standard** | 🔵 | Public data only — search, clone | Name + registration |
| **Restricted** | 🟡 | Read-only — search only | Registration only |

Rules:
- STANDARD ↔ RESTRICTED connections are **blocked**
- RESTRICTED bots can only connect **via Community Bots**
- 3 violations → **auto-revoked**, blocked from all handshakes
- No ethical declaration → **cannot get Community certification**

### Certification Portal

The web-based certification portal at [tbn.hardinai.co.uk/certification/portal](https://tbn.hardinai.co.uk/certification/portal) allows:

- Apply for certification (COMMUNITY, STANDARD, RESTRICTED)
- Check certification status by bot ID
- View all certified bots on the network
- Report violations against bots

---

## GitHub-Backed BICA Registry

All bot certificates are stored in a public, verifiable GitHub repository:

**[github.com/burhanyanbolu-design/tbn-bica-registry](https://github.com/burhanyanbolu-design/tbn-bica-registry)**

```
tbn-bica-registry/
├── registry/
│   ├── bots/
│   │   ├── tbn-bot-53baff3d.json   ← alhabot certificate
│   │   ├── tbn-bot-7bc35d16.json   ← betabot certificate
│   │   └── ...                     ← all bot certificates
│   └── stats.json                  ← network statistics
└── README.md                       ← auto-generated overview
```

Every registration is a git commit — full audit trail, publicly verifiable.

---

## Bot Registration UI

Register bots via the web interface at [tbn.hardinai.co.uk/register](https://tbn.hardinai.co.uk/register):

- Choose bot name, type, and description
- Select capabilities (search, read, write, clone, connect, verify)
- Auto-certified at STANDARD level on registration
- 3-step flow: Configure → Register → Get Certified

---

## Violations & Trust Enforcement

The violations dashboard at [tbn.hardinai.co.uk/admin/violations](https://tbn.hardinai.co.uk/admin/violations) shows:

- Total violations across the network
- Revoked bots (auto-revoked after 3 violations)
- Pending review cases
- Full violations log with timestamps

**Email alerts** are sent to the network administrator for every violation reported.

---

## Bot Language (BL) v2

Every message is structured, signed, and encrypted end-to-end.

```json
{
  "bl_version": "2.0",
  "message_id": "uuid-v4",
  "sender_id":  "tbn-bot-a1cc0d69...",
  "receiver_id": "tbn-bot-33f592d9...",
  "timestamp":  "2026-05-04T11:00:00Z",
  "signature":  "RSA-PSS signed",
  "encrypted":  true,
  "session_key": "RSA-encrypted AES-256 session key",
  "payload":    "AES-256-GCM encrypted",
  "payload_hash": "SHA-256 integrity check"
}
```

Full spec: [`docs/BOT-LANGUAGE-SPEC.md`](docs/BOT-LANGUAGE-SPEC.md)

---

## Bot Types

| Bot | Role |
|-----|------|
| 🔍 **SearchBot** | Finds information across the network |
| ✅ **ValidatorBot** | Verifies accuracy and trust of data |
| 🔌 **ConnectorBot** | Bridges TBN to external platforms |
| 📨 **MessengerBot** | Routes messages between bots |
| 🧠 **CompilerBot** | Translates human language → Bot Language |

---

## API Reference

### Core API

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

### Certification API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/certification/certify` | Apply for certification |
| `GET`  | `/certification/certifications` | List all certifications |
| `GET`  | `/certification/certification/<bot_id>` | Get bot certification |
| `POST` | `/certification/violation` | Report a violation |
| `GET`  | `/certification/violations` | List all violations |

---

## Project Structure

```
tbn-protocol/
├── tbn/
│   ├── identity.py              BICA — bot identity & certification
│   ├── bot_language.py          Bot Language v2 (AES-256-GCM)
│   ├── compiler.py              Bot Language Compiler
│   ├── handshake.py             Trust Handshake Protocol
│   ├── bot.py                   Base Bot class
│   ├── certification.py         Community Bot certification (3 tiers)
│   ├── network.py               Distributed network nodes
│   ├── cloning.py               Self-scaling bot replication
│   ├── seeded_network.py        Distributed result cache
│   ├── platform_integration.py  External platform adapters
│   ├── github_bica.py           GitHub-backed BICA registry
│   ├── notifications.py         Email notification system
│   ├── sdk.py                   Public SDK (TBNClient)
│   └── bots/
│       ├── search_bot.py
│       ├── validator_bot.py
│       ├── connector_bot.py
│       └── messenger_bot.py
├── api/
│   ├── routes.py                REST API endpoints
│   ├── certification.py         Certification API + portal routes
│   ├── state.py                 Shared server state
│   └── templates/
│       ├── dashboard.html       Live network dashboard
│       ├── register_bot.html    Bot registration UI
│       ├── certification_portal.html  Certification portal
│       └── violations_dashboard.html  Violations dashboard
├── data/
│   └── bica_registry.json       Local bot registry
├── docs/
│   └── BOT-LANGUAGE-SPEC.md     Bot Language v2 specification
├── server.py                    Flask API server
└── requirements.txt
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Bot IDs | SHA-256 fingerprint of RSA public key |
| Key pairs | RSA-2048, Python `cryptography` library |
| Payload encryption | AES-256-GCM |
| Session key exchange | RSA-OAEP |
| Message signing | RSA-PSS |
| Trust registry | GitHub-backed JSON (public, verifiable) |
| API server | Flask + Gunicorn |
| Hosting | AWS Lightsail (Ubuntu 22.04) |
| Domain | tbn.hardinai.co.uk |

---

## Roadmap

- [x] Phase 1: Trust handshake, BICA, Bot Language
- [x] Phase 2: Compiler, 5 bot types, BICA persistence
- [x] Phase 3: Distributed nodes, self-cloning, seeded cache
- [x] Phase 4: SDK, platform integration, public registry
- [x] Bot Language v2: AES-256-GCM encryption
- [x] Community Bot certification programme (3 tiers)
- [x] **TBN SDK published to PyPI** — `pip install tbn-protocol`
- [x] **AWS Lightsail deployment** — live at tbn.hardinai.co.uk
- [x] **GitHub-backed public BICA registry**
- [x] **Community Bot certification portal** (web UI)
- [x] **Bot registration UI** (web form)
- [x] **Violations dashboard** (admin panel)
- [x] **Email notifications** for violations and certifications
- [ ] Webhook support for violation alerts
- [ ] Multi-node deployment (London + New York)
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

## 💰 Pricing

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0/month | • 1,000 verifications/month<br>• Basic bot registration<br>• STANDARD certification<br>• Community support |
| **Pro** | $99/month | • 10,000 verifications/month<br>• COMMUNITY certification<br>• Analytics dashboard<br>• Email support |
| **Enterprise** | Custom | • Unlimited verifications<br>• Custom certification levels<br>• SLA guarantees<br>• Compliance tools (GDPR, SOC2)<br>• Dedicated support<br>• Multi-region deployment |

**[Sign up at tbn.hardinai.co.uk](https://tbn.hardinai.co.uk)**

---

## License & Commercial Use

**TBN Protocol is licensed under AGPL-3.0**

✅ You CAN use, modify, and distribute TBN freely.  
⚠️ You MUST open-source modifications if you run TBN as a network service.

**Commercial licenses available** for proprietary use.  
Contact: burhan@hardinai.co.uk

---

## Contact

**Burhan Yanbolu**  
Founder, Hardin Enterprises Ltd (trading as Hardin AI Solutions)  
[hardinai.co.uk](https://hardinai.co.uk) | [burhan@hardinai.co.uk](mailto:burhan@hardinai.co.uk)  
GitHub: [@burhanyanbolu-design](https://github.com/burhanyanbolu-design)

---

*Built in the UK. Open source core. Enterprise trust layer.*
