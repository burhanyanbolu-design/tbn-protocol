# TBN Protocol — Boomi Integration Guide

## Overview

TBN Protocol now integrates with **Boomi** as a trade partner. This integration allows Boomi processes to interact with TBN's trust infrastructure for AI agents.

## API Endpoints

### 1. Health Check (Public)

**Endpoint:** `GET /api/boomi/health`

No authentication required. Use this to verify the Boomi integration is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "TBN Protocol",
  "version": "1.0.0",
  "boomi_integration": "enabled",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

---

### 2. Process Handler (Protected)

**Endpoint:** `POST /api/boomi/process`

**Authentication:** Required — API key in `Authorization: Bearer tbn_live_xxxx` header

**Purpose:** Route Boomi documents to appropriate TBN handlers.

#### Request Body

```json
{
  "process_type": "bot_registration|certification_check|governance_query",
  "data": { /* process-specific data */ },
  "metadata": {
    "boomi_process_id": "unique-process-id",
    "timestamp": "2026-05-12T10:30:00Z",
    "source": "boomi"
  }
}
```

#### Response

```json
{
  "success": true,
  "process_id": "unique-process-id",
  "result": { /* handler-specific result */ },
  "status": "completed"
}
```

---

## Process Types

### A. Bot Registration

**Process Type:** `bot_registration`

Register a new bot with TBN Protocol.

**Request:**
```json
{
  "process_type": "bot_registration",
  "data": {
    "bot_name": "MyBot",
    "bot_type": "SEARCH|VALIDATOR|CONNECTOR|MESSENGER",
    "company": "Acme Corp",
    "email": "contact@acme.com",
    "description": "A search bot for product discovery"
  },
  "metadata": {
    "boomi_process_id": "proc-12345",
    "timestamp": "2026-05-12T10:30:00Z",
    "source": "boomi"
  }
}
```

**Response:**
```json
{
  "success": true,
  "process_id": "proc-12345",
  "result": {
    "bot_id": "tbn-bot-mybot-001",
    "bot_name": "MyBot",
    "bot_type": "SEARCH",
    "company": "Acme Corp",
    "status": "registered",
    "created_at": "2026-05-12T10:30:00Z"
  },
  "status": "completed"
}
```

---

### B. Certification Check

**Process Type:** `certification_check`

Verify the certification status of a bot.

**Request:**
```json
{
  "process_type": "certification_check",
  "data": {
    "bot_id": "tbn-bot-mybot-001",
    "cert_level": "GOLD"
  },
  "metadata": {
    "boomi_process_id": "proc-12346",
    "timestamp": "2026-05-12T10:35:00Z",
    "source": "boomi"
  }
}
```

**Response:**
```json
{
  "success": true,
  "process_id": "proc-12346",
  "result": {
    "bot_id": "tbn-bot-mybot-001",
    "certified": true,
    "cert_level": "GOLD",
    "expires": "2027-05-12T10:35:00Z",
    "verified_at": "2026-05-12T10:35:00Z"
  },
  "status": "completed"
}
```

---

### C. Governance Query

**Process Type:** `governance_query`

Query governance status, violations, or access requests.

**Request:**
```json
{
  "process_type": "governance_query",
  "data": {
    "query_type": "bot_status|violations|access_requests",
    "bot_id": "tbn-bot-mybot-001",
    "limit": 10
  },
  "metadata": {
    "boomi_process_id": "proc-12347",
    "timestamp": "2026-05-12T10:40:00Z",
    "source": "boomi"
  }
}
```

**Response (bot_status):**
```json
{
  "success": true,
  "process_id": "proc-12347",
  "result": {
    "query_type": "bot_status",
    "count": 1,
    "bots": [
      {
        "bot_id": "tbn-bot-mybot-001",
        "bot_name": "MyBot",
        "company": "Acme Corp",
        "status": "active"
      }
    ]
  },
  "status": "completed"
}
```

---

## Authentication

All protected endpoints require an API key. Get one by:

1. **Request a trial key** via `POST /api/access/request`
2. **Use the key** in the `Authorization` header:
   ```
   Authorization: Bearer tbn_live_xxxx
   ```

### Subscription Tiers

| Tier | Price | Calls/Day | Bots | Features |
|------|-------|-----------|------|----------|
| TRIAL | Free | 100 | 3 | Read-only, basic search |
| STARTER | £99/mo | 1,000 | 10 | Read-only, sports/financial data |
| PRO | £299/mo | 10,000 | All | Read-write, real-time, webhooks |
| ENTERPRISE | Custom | Unlimited | All | Dedicated support, SLA |

---

## Error Handling

All errors return a JSON response with `success: false`:

```json
{
  "success": false,
  "error": "Description of what went wrong",
  "status": "error"
}
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `process_type is required` | Missing process_type field | Add `process_type` to request |
| `Unknown process_type: xxx` | Invalid process type | Use one of: `bot_registration`, `certification_check`, `governance_query` |
| `bot_id is required` | Missing bot_id for certification check | Add `bot_id` to data |
| `Bot not found: xxx` | Bot doesn't exist in registry | Verify bot_id is correct |
| `Invalid bot_type: xxx` | Unknown bot type | Use: `SEARCH`, `VALIDATOR`, `CONNECTOR`, `MESSENGER` |

---

## Boomi Configuration

### In Boomi Process

1. **Add HTTP Connector**
   - Method: `POST`
   - URL: `https://tbn.hardinai.co.uk/api/boomi/process`
   - Headers:
     - `Authorization: Bearer tbn_live_xxxx`
     - `Content-Type: application/json`

2. **Map Input Document**
   - Transform your Boomi document to match the request format above

3. **Map Output Document**
   - Extract `result` from the response for downstream processing

4. **Error Handling**
   - Check `success` field
   - If `false`, use `error` field for logging/alerts

---

## Example Boomi Process Flow

```
[Input Document]
    ↓
[Map to TBN Request]
    ↓
[HTTP POST to /api/boomi/process]
    ↓
[Check success field]
    ├─ true → [Extract result] → [Continue]
    └─ false → [Log error] → [Alert]
```

---

## Support

- **Email:** info@hardinai.co.uk
- **Dashboard:** https://tbn.hardinai.co.uk
- **GitHub:** https://github.com/burhanyanbolu-design/tbn-protocol
- **License:** AGPL-3.0 with commercial licensing

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-12 | Initial Boomi integration release |

