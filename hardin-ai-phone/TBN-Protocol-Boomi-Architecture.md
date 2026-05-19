# TBN Protocol — Boomi Integration Architecture

**Company:** Hardin Enterprises Ltd  
**Product:** TBN Protocol  
**Version:** 1.0.0  
**Date:** May 2026  
**Contact:** burhan@hardinai.co.uk

---

## Overview

TBN Protocol is a trust infrastructure for AI agents. It provides a standardised REST API for enterprises to register, certify, and govern AI bots operating within their systems.

The Boomi integration enables users to verify bot certifications, register new AI agents, and enforce governance policies directly within their Boomi integration workflows.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    BOOMI PLATFORM                            │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Source App  │───▶│ Boomi Process │───▶│ Target App   │  │
│  └─────────────┘    └──────┬───────┘    └──────────────┘  │
│                            │                                │
│                            │ HTTP Client Connector          │
│                            ▼                                │
└────────────────────────────┼────────────────────────────────┘
                             │
                             │ HTTPS (REST API)
                             │ Header: X-API-Key
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                TBN PROTOCOL SERVER                           │
│                https://tbn.hardinai.co.uk                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  API Gateway (Flask/Gunicorn)                       │   │
│  │  ├─ /api/boomi/bot_registration                     │   │
│  │  ├─ /api/boomi/certification_check                  │   │
│  │  └─ /api/boomi/governance_query                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  TBN Core Engine                                    │   │
│  │  ├─ Bot Registry (BICA)                             │   │
│  │  ├─ Certification Authority                         │   │
│  │  ├─ Governance Engine                               │   │
│  │  └─ Audit Logger                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Database                                           │   │
│  │  ├─ Bot registrations                               │   │
│  │  ├─ Certifications                                  │   │
│  │  ├─ Governance policies                             │   │
│  │  └─ Audit logs                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### 1. Bot Registration

**POST** `/api/boomi/bot_registration`

Registers a new AI agent with the TBN Protocol.

**Request:**
```json
{
  "bot_name": "CustomerServiceBot",
  "bot_type": "search",
  "capabilities": ["text_generation", "data_retrieval"],
  "owner": "Acme Corp"
}
```

**Response:**
```json
{
  "status": "success",
  "bot_id": "tbn_bot_abc123",
  "registration_status": "registered",
  "certificate": "CERT-2026-001",
  "created_at": "2026-05-13T10:00:00Z"
}
```

### 2. Certification Check

**POST** `/api/boomi/certification_check`

Verifies if an AI bot is certified and trusted.

**Request:**
```json
{
  "bot_id": "tbn_bot_abc123"
}
```

**Response:**
```json
{
  "status": "success",
  "bot_id": "tbn_bot_abc123",
  "certification_status": "certified",
  "trust_level": "high",
  "expiry_date": "2027-05-13",
  "issuer": "TBN Certification Authority"
}
```

### 3. Governance Query

**POST** `/api/boomi/governance_query`

Queries governance policies and compliance rules.

**Request:**
```json
{
  "query_type": "compliance_check",
  "bot_id": "tbn_bot_abc123"
}
```

**Response:**
```json
{
  "status": "success",
  "bot_id": "tbn_bot_abc123",
  "compliance_status": "compliant",
  "policies_applied": ["data_privacy", "rate_limiting", "audit_logging"],
  "violations": []
}
```

---

## Authentication

All API requests require an API key passed in the `X-API-Key` header.

```
X-API-Key: tbn_live_rHwyKxafnTomRS70ZjSKcYbI6IyGWyKR
```

API keys are issued per organisation and can be requested at info@hardinai.co.uk.

---

## Boomi Connection Setup

1. Create a new **HTTP Client** connection
2. Set URL: `https://tbn.hardinai.co.uk/api/boomi`
3. Add Request Header: `X-API-Key` = your API key
4. Content-Type: `application/json`
5. Create operations for each endpoint (POST)
6. Map JSON request/response profiles

---

## Security

- HTTPS/TLS 1.3 encryption in transit
- API key authentication
- Rate limiting (100 requests/day on trial tier)
- IP allowlisting available on enterprise tier
- Full audit logging of all API calls

---

## Infrastructure

- **Hosting:** AWS Lightsail (London region)
- **Server:** Ubuntu 22.04 LTS
- **Application:** Python Flask + Gunicorn
- **Database:** SQLite (production: PostgreSQL)
- **Uptime SLA:** 99.5%
- **Response Time:** < 500ms average

---

## Support

| Level | Provider | Contact |
|-------|----------|---------|
| L1 | Boomi | Boomi Support |
| L2 | Hardin Enterprises | burhan@hardinai.co.uk |
| Escalation | CEO | +447740304061 |

**Support Hours:** 09:00–18:00 GMT, Monday–Friday  
**Response SLA:** 24 hours (business days)

---

## Links

- Live Platform: https://tbn.hardinai.co.uk
- GitHub: https://github.com/burhanyanbolu-design/tbn-protocol
- PyPI Package: https://pypi.org/project/tbn-protocol/
- Company: https://hardinai.co.uk

---

*Document Version 1.0 — May 2026*  
*Hardin Enterprises Ltd — Company No. registered in England and Wales*
