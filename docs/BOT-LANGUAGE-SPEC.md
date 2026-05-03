# Bot Language (BL) Specification
## Version 2.0

**Author:** Burhan Yanbolu  
**Status:** Active  
**Date:** May 2026

---

## What is Bot Language?

Bot Language (BL) is the native communication protocol for TBN agents.  
It is the "internet language for AI agents" — structured, encrypted, signed, and universally interpretable by any bot on the network.

> Think: JSON + AES encryption + RSA signatures + intent logic

Humans speak English. Bots speak Bot Language.  
The **Bot Language Compiler** translates human input → BL at the entry point.  
Bot-to-bot communication is **native BL** — no translation needed.

---

## Message Structure

Every BL message has two layers:

```
┌─────────────────────────────────────────────────────┐
│  ENVELOPE (plaintext — routing metadata)            │
│  ┌───────────────────────────────────────────────┐  │
│  │  PAYLOAD (AES-256 encrypted — actual content) │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Full Message Schema

```json
{
  "bl_version": "2.0",
  "message_id": "<uuid-v4>",
  "sender_id":  "tbn-bot-<sha256-fingerprint>",
  "receiver_id": "tbn-bot-<sha256-fingerprint>",
  "timestamp":  "2026-05-03T00:00:00Z",
  "signature":  "<base64 RSA-PSS signature of envelope>",
  "encrypted":  true,
  "session_key": "<base64 AES session key, RSA-encrypted with receiver public key>",
  "payload":    "<base64 AES-256-GCM encrypted payload>",
  "payload_hash": "<sha256 of plaintext payload — integrity check>"
}
```

### Decrypted Payload Schema

```json
{
  "INTENT":      "SEARCH",
  "TARGET":      "VERIFIED_SOURCES",
  "TRUST_LEVEL": "HIGH",
  "DATA_TYPE":   "AI_TOOLS",
  "QUERY":       "Find trusted AI tools for small businesses",
  "FILTERS":     { "audience": "small_business" },
  "PRIORITY":    1,
  "RESPONSE":    null
}
```

---

## Intent Types

| Intent | Description | Direction |
|--------|-------------|-----------|
| `SEARCH` | Find information | Human → Bot, Bot → Bot |
| `DATA_REQUEST` | Request specific data | Bot → Bot |
| `DATA_RESPONSE` | Return data | Bot → Bot |
| `HANDSHAKE_INIT` | Start trust handshake | Bot → Bot |
| `HANDSHAKE_ACCEPT` | Accept handshake | Bot → Bot |
| `HANDSHAKE_COMPLETE` | Confirm trust established | Bot → Bot |
| `VALIDATE` | Request data validation | Bot → Bot |
| `VALIDATE_RESPONSE` | Return validation result | Bot → Bot |
| `COMPILE` | Request NL → BL compilation | Human → CompilerBot |
| `COMPILE_RESPONSE` | Return compiled BL message | CompilerBot → Bot |
| `PING` | Network health check | Bot → Bot |
| `PONG` | Health check response | Bot → Bot |
| `ERROR` | Error notification | Bot → Bot |
| `CLONE_REQUEST` | Request bot clone | Bot → CloneManager |
| `CLONE_READY` | Clone is ready | CloneManager → Bot |

---

## Trust Levels

| Level | Meaning | Access |
|-------|---------|--------|
| `HIGH` | Certified Community Bot | Full access to verified sources |
| `MEDIUM` | Standard Bot | Public data only |
| `LOW` | Restricted Bot | Read-only, limited queries |
| `NONE` | Unverified | No access |

---

## Target Types

| Target | Description |
|--------|-------------|
| `VERIFIED_SOURCES` | Only BICA-certified data sources |
| `PUBLIC_SOURCES` | Any public data |
| `RESTRICTED` | Private/permissioned data |
| `NETWORK` | Other bots on the TBN network |
| `PLATFORM` | External platform (GitHub, Notion etc.) |

---

## Data Types

| Type | Description |
|------|-------------|
| `AI_TOOLS` | AI tools, platforms, models |
| `CODE` | Code, repositories, libraries |
| `DATA` | Datasets, databases |
| `DOCS` | Documentation, guides |
| `NEWS` | News, articles, updates |
| `GENERAL` | Unclassified |

---

## Encryption

### Payload Encryption (AES-256-GCM)

1. Sender generates a random 256-bit AES session key
2. Payload is encrypted with AES-256-GCM
3. Session key is encrypted with receiver's RSA public key
4. Both are included in the message envelope

### Message Signing (RSA-PSS)

The envelope (excluding payload) is signed with the sender's RSA private key.  
Receiver verifies signature before decrypting payload.

### Flow

```
Sender                              Receiver
  │                                    │
  │  1. Generate AES session key       │
  │  2. Encrypt payload (AES-GCM)      │
  │  3. Encrypt session key (RSA pub)  │
  │  4. Sign envelope (RSA priv)       │
  │                                    │
  │ ──── encrypted BL message ──────► │
  │                                    │
  │                  5. Verify sig     │
  │                  6. Decrypt key    │
  │                  7. Decrypt payload│
  │                  8. Process intent │
```

---

## Compiler

The **Bot Language Compiler** is the only translation layer.  
It sits at the human entry point and converts natural language → BL.

```
Human: "Find trusted AI tools for small businesses"
         │
         ▼
   ┌─────────────┐
   │  BL Compiler │
   └─────────────┘
         │
         ▼
{
  "INTENT":      "SEARCH",
  "TARGET":      "VERIFIED_SOURCES",
  "TRUST_LEVEL": "HIGH",
  "DATA_TYPE":   "AI_TOOLS",
  "QUERY":       "Find trusted AI tools for small businesses",
  "FILTERS":     { "audience": "SMALL_BUSINESS" },
  "PRIORITY":    2
}
```

**Key rule:** Once compiled, bots speak BL natively.  
No re-compilation happens inside the network.

---

## Example: Full End-to-End Message Flow

```
1. Human types: "Find trusted AI tools for small businesses"
2. CompilerBot compiles → BL message (INTENT=SEARCH)
3. BL message encrypted with SearchBot's public key
4. SearchBot receives, verifies signature, decrypts payload
5. SearchBot executes search, creates DATA_RESPONSE BL message
6. DATA_RESPONSE encrypted with ValidatorBot's public key
7. ValidatorBot verifies, validates results
8. Validated results returned to human in plain English
```

---

## Versioning

| Version | Status | Changes |
|---------|--------|---------|
| `1.0` | Deprecated | Basic JSON, RSA signing only |
| `2.0` | **Current** | AES-256-GCM payload encryption, session keys, TARGET field, CompilerBot |

---

## BL v1 → v2 Migration

| Field | v1 | v2 |
|-------|----|----|
| `bl_version` | `"1.0"` | `"2.0"` |
| `encrypted` | not present | `true` |
| `session_key` | not present | RSA-encrypted AES key |
| `payload` | plaintext JSON | AES-256-GCM encrypted |
| `payload_hash` | not present | SHA-256 integrity check |
| `receiver_id` | not present | required for encryption |
| `TARGET` | not present | required in payload |

---

*This is a living specification. Update as the protocol evolves.*
