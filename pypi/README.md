# TBN Protocol — Python SDK

> **Trust infrastructure for AI agents. Think HTTPS for bots.**

[![PyPI version](https://badge.fury.io/py/tbn-protocol.svg)](https://badge.fury.io/py/tbn-protocol)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## Install

```bash
pip install tbn-protocol
```

## Quick Start

```python
from tbn import TBNClient

# Register your bot (one time)
client = TBNClient(bot_name="MyBot", bot_type="SEARCH")
client.register()

# Search (automatic handshake + verification)
results = client.search("Find AI tools for small businesses")
for r in results["results"]:
    print(r["name"], r["url"])

# Verify another bot
trusted = client.verify("tbn-bot-xxxx")
print("Trusted:", trusted)

# Trust handshake with another bot
result = client.handshake("tbn-bot-yyyy")
print(result["status"])  # TRUST_ESTABLISHED
```

## What is TBN Protocol?

TBN Protocol gives every AI agent a cryptographic identity and a way to prove it.

**The Problem:** AI agents are everywhere — ChatGPT plugins, AutoGPT, LangChain agents. But when agents from different companies communicate, there's no standard way to verify who they're talking to.

**The Solution:** TBN gives every bot:
- A cryptographic certificate (RSA-2048)
- A 3-step trust handshake protocol
- AES-256-GCM encrypted communication
- Three trust tiers (COMMUNITY, STANDARD, RESTRICTED)

## Bot Types

| Type | Role |
|------|------|
| `SEARCH` | Finds information across the network |
| `VALIDATOR` | Verifies accuracy and trust of data |
| `CONNECTOR` | Bridges TBN to external platforms |
| `MESSENGER` | Routes messages between bots |

## Full Example

```python
from tbn import TBNClient

# Register two bots
bot_a = TBNClient("AlphaBot", "SEARCH")
bot_a.register()

bot_b = TBNClient("BetaBot", "VALIDATOR")
bot_b.register()

# Trust handshake
result = bot_a.handshake(bot_b.bot_id)
print(result["status"])  # TRUST_ESTABLISHED

# Search
results = bot_a.search("Find trusted AI tools")
print(results["count"], "results found")

# Upgrade to COMMUNITY certification
bot_a.certify(
    level="COMMUNITY",
    purpose="Trusted AI tool discovery",
    ethical_declaration=True
)

# Network stats
stats = bot_a.stats()
print(stats["registered_bots"], "bots on network")
```

## Live Demo

Try the live TBN network: **https://tbn.hardinai.co.uk**

## License

AGPL-3.0 — Commercial licenses available at **burhan@hardinai.co.uk**

## Links

- **Website**: https://tbn.hardinai.co.uk
- **GitHub**: https://github.com/burhanyanbolu-design/tbn-protocol
- **Contact**: burhan@hardinai.co.uk
