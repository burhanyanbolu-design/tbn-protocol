# 🏗️ Boomi Integration — Architecture & Flow

**Date**: May 12, 2026  
**Version**: 1.0.0

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BOOMI PLATFORM                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Boomi Process (Web Services Server Connector)           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ 1. Receive request from Boomi customer             │  │  │
│  │  │ 2. Add Authorization header (API key)              │  │  │
│  │  │ 3. POST to /api/boomi/process                      │  │  │
│  │  │ 4. Receive JSON response                           │  │  │
│  │  │ 5. Return documents to Boomi                       │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    HTTPS POST Request
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    TBN PROTOCOL SERVER                          │
│                  (AWS Lightsail 3.11.229.68)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Flask API (Gunicorn)                                    │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ POST /api/boomi/process                            │  │  │
│  │  │ ├─ Validate API key                                │  │  │
│  │  │ ├─ Parse request body                              │  │  │
│  │  │ ├─ Route to process handler                        │  │  │
│  │  │ └─ Return JSON response                            │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  Process Handlers:                                        │  │
│  │  ├─ _boomi_register_bot()                                │  │
│  │  ├─ _boomi_check_certification()                         │  │
│  │  └─ _boomi_governance_query()                            │  │
│  │                                                            │  │
│  │  GET /api/boomi/health                                   │  │
│  │  └─ Return health status (no auth required)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  TBN Core Systems                                        │  │
│  │  ├─ Bot Registry (state.bots)                            │  │
│  │  ├─ Certification Authority                             │  │
│  │  ├─ Governance Engine                                   │  │
│  │  └─ Access Control                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    HTTPS JSON Response
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        BOOMI PLATFORM                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Response Processing                                     │  │
│  │  ├─ Parse JSON response                                 │  │
│  │  ├─ Extract result data                                 │  │
│  │  ├─ Return documents to customer                        │  │
│  │  └─ Log transaction                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request/Response Flow

### 1. Bot Registration Flow

```
Boomi Customer
      ↓
[Boomi Process]
      ↓
POST /api/boomi/process
{
  "process_type": "bot_registration",
  "data": {
    "bot_name": "MyBot",
    "bot_type": "SEARCH",
    "company": "My Company",
    "email": "contact@company.com",
    "description": "My bot"
  }
}
      ↓
[TBN API]
      ↓
_boomi_register_bot()
      ↓
[Bot Registry]
      ↓
Create new bot
      ↓
Return response
{
  "success": true,
  "result": {
    "bot_id": "tbn-bot-xxxxx",
    "bot_name": "MyBot",
    "status": "registered",
    "created_at": "2026-05-12T..."
  }
}
      ↓
[Boomi Process]
      ↓
Boomi Customer
```

### 2. Governance Query Flow

```
Boomi Customer
      ↓
[Boomi Process]
      ↓
POST /api/boomi/process
{
  "process_type": "governance_query",
  "data": {
    "query_type": "bot_status",
    "limit": 10
  }
}
      ↓
[TBN API]
      ↓
_boomi_governance_query()
      ↓
[Bot Registry]
      ↓
Query bots
      ↓
Return response
{
  "success": true,
  "result": {
    "query_type": "bot_status",
    "count": 1,
    "bots": [{"bot_id": "tbn-bot-xxxxx"}]
  }
}
      ↓
[Boomi Process]
      ↓
Boomi Customer
```

### 3. Certification Check Flow

```
Boomi Customer
      ↓
[Boomi Process]
      ↓
POST /api/boomi/process
{
  "process_type": "certification_check",
  "data": {
    "bot_id": "tbn-bot-xxxxx",
    "cert_level": "GOLD"
  }
}
      ↓
[TBN API]
      ↓
_boomi_check_certification()
      ↓
[Certification Authority]
      ↓
Verify certificate
      ↓
Return response
{
  "success": true,
  "result": {
    "bot_id": "tbn-bot-xxxxx",
    "certified": true,
    "cert_level": "GOLD",
    "verified_at": "2026-05-12T..."
  }
}
      ↓
[Boomi Process]
      ↓
Boomi Customer
```

---

## 🔐 Authentication Flow

```
Boomi Process
      ↓
Add Authorization Header
Authorization: Bearer tbn_live_rHwyKxafnTomRS70ZjSKcYbI6IyGWyKR
      ↓
POST /api/boomi/process
      ↓
[TBN API]
      ↓
Extract API key from header
      ↓
[Access Control]
      ↓
Validate API key
      ├─ Key format valid?
      ├─ Key exists?
      ├─ Key not expired?
      └─ Rate limit not exceeded?
      ↓
✅ Valid → Process request
❌ Invalid → Return 401 Unauthorized
```

---

## 📊 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    BOOMI PLATFORM                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Web Services Server Connector                         │  │
│  │  ├─ URL: https://tbn.hardinai.co.uk/api/boomi/process │  │
│  │  ├─ Method: POST                                       │  │
│  │  ├─ Content-Type: application/json                    │  │
│  │  └─ Authorization: Bearer tbn_live_xxxxx              │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                          ↕ HTTPS
┌──────────────────────────────────────────────────────────────┐
│                    TBN PROTOCOL                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  API Routes (api/routes.py)                            │  │
│  │  ├─ boomi_process()                                    │  │
│  │  │  ├─ Validate API key                                │  │
│  │  │  ├─ Parse request                                   │  │
│  │  │  ├─ Route to handler                                │  │
│  │  │  └─ Return response                                 │  │
│  │  │                                                      │  │
│  │  └─ boomi_health()                                     │  │
│  │     └─ Return health status                            │  │
│  └────────────────────────────────────────────────────────┘  │
│                          ↕                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Process Handlers                                      │  │
│  │  ├─ _boomi_register_bot()                              │  │
│  │  ├─ _boomi_check_certification()                       │  │
│  │  └─ _boomi_governance_query()                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                          ↕                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  TBN Core Systems                                      │  │
│  │  ├─ Bot Registry                                       │  │
│  │  ├─ Certification Authority                           │  │
│  │  ├─ Governance Engine                                 │  │
│  │  └─ Access Control                                    │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔌 Integration Points

### Boomi Side
- **Connector**: Web Services Server Connector
- **URL**: `https://tbn.hardinai.co.uk/api/boomi/process`
- **Method**: POST
- **Headers**: 
  - `Authorization: Bearer tbn_live_xxxxx`
  - `Content-Type: application/json`
- **Request Profile**: JSON (boomi_request_profile.json)
- **Response Profile**: JSON (boomi_response_profile.json)

### TBN Side
- **Endpoint**: `/api/boomi/process`
- **Handler**: `boomi_process()` in `api/routes.py`
- **Authentication**: API key validation
- **Process Types**: bot_registration, certification_check, governance_query
- **Response Format**: JSON with success/error status

---

## 📈 Scalability

### Current Capacity
- **API Key Tier**: TRIAL (100 calls/day)
- **Concurrent Connections**: Limited by Gunicorn workers
- **Response Time**: <500ms typical
- **Uptime**: 99.9% (AWS Lightsail)

### Upgrade Path
1. **STARTER** (£99/mo) — 1,000 calls/day
2. **PRO** (£299/mo) — 10,000 calls/day
3. **ENTERPRISE** (Custom) — Unlimited calls/day

### Scaling Options
- Increase Gunicorn workers
- Add load balancer
- Implement caching
- Add database for persistence
- Set up monitoring/alerts

---

## 🔒 Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    HTTPS Layer                          │
│  ├─ TLS 1.2+ encryption                                │
│  ├─ Certificate validation                             │
│  └─ Secure communication                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 Authentication Layer                    │
│  ├─ API key validation                                 │
│  ├─ Bearer token format check                          │
│  ├─ Key expiry check                                   │
│  └─ Rate limiting                                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Validation Layer                       │
│  ├─ Input validation                                   │
│  ├─ JSON schema validation                             │
│  ├─ Field type checking                                │
│  └─ Required field checking                            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Processing Layer                       │
│  ├─ Bot registration                                   │
│  ├─ Certification checking                             │
│  ├─ Governance queries                                 │
│  └─ Error handling                                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Response Layer                        │
│  ├─ JSON formatting                                    │
│  ├─ Error messages                                     │
│  ├─ Status codes                                       │
│  └─ Logging                                            │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 API Endpoints Summary

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/boomi/process` | POST | ✅ Required | Main process handler |
| `/api/boomi/health` | GET | ❌ Not required | Health check |

---

## 🔄 Process Types

| Type | Purpose | Input | Output |
|------|---------|-------|--------|
| `bot_registration` | Register new bot | bot_name, bot_type, company, email, description | bot_id, status |
| `certification_check` | Check certification | bot_id, cert_level | certified, cert_level, expires |
| `governance_query` | Query governance | query_type, bot_id (optional), limit | count, results |

---

## 📝 Request/Response Examples

### Request Format
```json
{
  "process_type": "bot_registration",
  "data": {
    "bot_name": "MyBot",
    "bot_type": "SEARCH",
    "company": "My Company",
    "email": "contact@company.com",
    "description": "My bot"
  },
  "metadata": {
    "boomi_process_id": "proc-123",
    "timestamp": "2026-05-12T10:30:00Z",
    "source": "boomi"
  }
}
```

### Response Format (Success)
```json
{
  "success": true,
  "process_id": "boomi-proc-001",
  "status": "completed",
  "result": {
    "bot_id": "tbn-bot-xxxxx",
    "bot_name": "MyBot",
    "status": "registered",
    "created_at": "2026-05-12T10:30:00Z"
  }
}
```

### Response Format (Error)
```json
{
  "success": false,
  "error": "Bad Request",
  "reason": "bot_id is required",
  "status": "error"
}
```

---

## 🎯 Key Design Decisions

### 1. Web Services Server Connector
- **Why**: Cleaner than Documents step
- **Benefit**: Easier to configure and maintain
- **Alternative**: HTTP Client Connector (more complex)

### 2. Bearer Token Authentication
- **Why**: Industry standard
- **Benefit**: Secure and widely supported
- **Format**: `Authorization: Bearer tbn_live_xxxxx`

### 3. JSON Request/Response
- **Why**: Universal format
- **Benefit**: Easy to parse and validate
- **Alternative**: XML (less common)

### 4. Stateless API
- **Why**: Scalable and simple
- **Benefit**: No session management needed
- **Trade-off**: Each request must include all needed data

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Lightsail                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Ubuntu 22.04 (3.11.229.68)                       │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │  Nginx (Reverse Proxy)                      │  │  │
│  │  │  ├─ Port 80/443                             │  │  │
│  │  │  ├─ SSL/TLS termination                     │  │  │
│  │  │  └─ Route to Gunicorn                       │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  │                      ↓                             │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │  Gunicorn (WSGI Server)                     │  │  │
│  │  │  ├─ Workers: 1-4                            │  │  │
│  │  │  ├─ Port 5004                               │  │  │
│  │  │  └─ Flask application                       │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  │                      ↓                             │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │  Flask Application                          │  │  │
│  │  │  ├─ api/routes.py                           │  │  │
│  │  │  ├─ Boomi endpoints                         │  │  │
│  │  │  └─ TBN core systems                        │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 📞 Support & Monitoring

### Health Monitoring
```bash
# Check service status
sudo systemctl status tbn

# Check health endpoint
curl https://tbn.hardinai.co.uk/api/boomi/health

# View logs
sudo journalctl -u tbn -f
```

### Metrics to Monitor
- API response time
- Error rate
- API key usage
- Uptime percentage
- Request volume

---

## 🎓 Architecture Benefits

1. **Scalability** — Stateless design allows horizontal scaling
2. **Security** — Multiple layers of authentication and validation
3. **Reliability** — Error handling and logging
4. **Maintainability** — Clear separation of concerns
5. **Extensibility** — Easy to add new process types
6. **Performance** — Optimized for fast response times

---

**Architecture Version**: 1.0.0  
**Last Updated**: May 12, 2026  
**Status**: ✅ PRODUCTION READY

