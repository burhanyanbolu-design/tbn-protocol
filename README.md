# TBN Protocol — Trusted Bot Network

> The trust and identity layer for AI agents. Think HTTPS, but for bots.

**Author:** Burhan Yanbolu  
**Status:** Phase 1 MVP  
**Version:** 0.1.0

---

## What is TBN?

AI agents currently have no standard way to:
- Verify who they are talking to
- Communicate securely with other agents
- Access restricted platforms with permission

TBN solves this with three core components:

1. **Bot Identity & Certification Authority (BICA)** — every bot gets a cryptographic identity (public/private key pair)
2. **Bot Language (BL)** — a structured, encrypted JSON protocol for agent-to-agent communication
3. **Trust Handshake Protocol** — bots verify each other before any data exchange (like HTTPS but for AI agents)

---

## Phase 1 MVP

Two bots performing a full trust handshake and exchanging encrypted data.

```
Bot A                    BICA                    Bot B
  |                        |                       |
  |-- "Here is my ID" ---->|                       |
  |                        |-- "Verified" -------->|
  |<---------------------------------------- "Here is my ID"
  |-- "Verified" --------->|                       |
  |<------------------------------------------------|
  |         Encrypted channel established           |
  |<=============== Data Exchange ================>|
```

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the demo (two bots doing a full trust handshake)
python demo.py
```

---

## Project Structure

```
tbn-protocol/
├── tbn/
│   ├── __init__.py
│   ├── identity.py        # Bot identity & key generation (BICA)
│   ├── bot_language.py    # Bot Language (BL) message schema
│   ├── handshake.py       # Trust Handshake Protocol
│   └── bot.py             # Base Bot class
├── demo.py                # Phase 1 demo: two bots handshaking
├── requirements.txt
└── README.md
```

---

## Architecture

See [TBN Architecture](docs/TBN-ARCHITECTURE.md) for the full 8-layer design.

---

## Roadmap

- [x] Phase 1: Two bots, trust handshake, encrypted data exchange
- [ ] Phase 2: Bot Language Compiler, BICA registry, 4 bot types
- [ ] Phase 3: Distributed routing, self-cloning under load
- [ ] Phase 4: External platform integration, open SDK
