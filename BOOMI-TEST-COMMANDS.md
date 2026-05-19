# 🧪 Boomi Integration — Quick Test Commands

**API Key**: `tbn_live_rHwyKxafnTomRS70ZjSKcYbI6IyGWyKR`  
**Endpoint**: `https://tbn.hardinai.co.uk/api/boomi/process`  
**Date**: May 12, 2026

---

## 1️⃣ Health Check (No Auth Required)

```bash
curl -X GET https://tbn.hardinai.co.uk/api/boomi/health
```

**Expected Response:**
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

## 2️⃣ Register a Bot

```bash
curl -X POST https://tbn.hardinai.co.uk/api/boomi/process \
  -H "Authorization: Bearer tbn_live_rHwyKxafnTomRS70ZjSKcYbI6IyGWyKR" \
  -H "Content-Type: application/json" \
  -d '{
    "process_type": "bot_registration",
    "data": {
      "bot_name": "TestBot",
      "bot_type": "SEARCH",
      "company": "Test Company",
      "email": "test@company.com",
      "description": "Test bot for verification"
    }
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "process_id": "boomi-test-001",
  "status": "completed",
  "result": {
    "bot_id": "tbn-bot-xxxxx",
    "bot_name": "TestBot",
    "bot_type": "SEARCH",
    "company": "Test Company",
    "status": "registered",
    "created_at": "2026-05-12T10:30:00Z"
  }
}
```

**Save the bot_id for next tests!**

---

## 3️⃣ Query Bot Status

```bash
curl -X POST https://tbn.hardinai.co.uk/api/boomi/process \
  -H "Authorization: Bearer tbn_live_rHwyKxafnTomRS70ZjSKcYbI6IyGWyKR" \
  -H "Content-Type: application/json" \
  -d '{
    "process_type": "governance_query",
    "data": {
      "query_type": "bot_status",
      "limit": 10
    }
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "process_id": "boomi-query-001",
  "status": "completed",
  "result": {
    "query_type": "bot_status",
    "count": 1,
    "bots": [
      {
        "bot_id": "tbn-bot-xxxxx"
      }
    ]
  }
}
```

---

## 4️⃣ Check Certification Status

Replace `tbn-bot-xxxxx` with the bot_id from step 2.

```bash
curl -X POST https://tbn.hardinai.co.uk/api/boomi/process \
  -H "Authorization: Bearer tbn_live_rHwyKxafnTomRS70ZjSKcYbI6IyGWyKR" \
  -H "Content-Type: application/json" \
  -d '{
    "process_type": "certification_check",
    "data": {
      "bot_id": "tbn-bot-xxxxx",
      "cert_level": "GOLD"
    }
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "process_id": "boomi-cert-001",
  "status": "completed",
  "result": {
    "bot_id": "tbn-bot-xxxxx",
    "certified": true,
    "cert_level": "GOLD",
    "verified_at": "2026-05-12T10:30:00Z"
  }
}
```

---

## 5️⃣ Query Violations (Optional)

```bash
curl -X POST https://tbn.hardinai.co.uk/api/boomi/process \
  -H "Authorization: Bearer tbn_live_rHwyKxafnTomRS70ZjSKcYbI6IyGWyKR" \
  -H "Content-Type: application/json" \
  -d '{
    "process_type": "governance_query",
    "data": {
      "query_type": "violations",
      "limit": 10
    }
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "process_id": "boomi-violations-001",
  "status": "completed",
  "result": {
    "query_type": "violations",
    "count": 0,
    "violations": []
  }
}
```

---

## 6️⃣ Query Access Requests (Optional)

```bash
curl -X POST https://tbn.hardinai.co.uk/api/boomi/process \
  -H "Authorization: Bearer tbn_live_rHwyKxafnTomRS70ZjSKcYbI6IyGWyKR" \
  -H "Content-Type: application/json" \
  -d '{
    "process_type": "governance_query",
    "data": {
      "query_type": "access_requests",
      "limit": 10
    }
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "process_id": "boomi-requests-001",
  "status": "completed",
  "result": {
    "query_type": "access_requests",
    "count": 0,
    "requests": []
  }
}
```

---

## ❌ Error Responses

### Invalid API Key
```json
{
  "error": "Unauthorized",
  "reason": "Invalid key format",
  "upgrade": "https://tbn.hardinai.co.uk/pricing"
}
```

### Missing Required Field
```json
{
  "error": "Bad Request",
  "reason": "bot_id is required",
  "status": "error"
}
```

### Bot Not Found
```json
{
  "error": "Not Found",
  "reason": "Bot not found: tbn-bot-invalid",
  "status": "error"
}
```

---

## 📝 Testing Checklist

- [ ] Health check returns healthy status
- [ ] Bot registration creates a new bot
- [ ] Bot status query returns the registered bot
- [ ] Certification check returns valid response
- [ ] Violations query returns empty list
- [ ] Access requests query returns empty list
- [ ] All responses have correct JSON format
- [ ] All responses include success/error status

---

## 🔑 API Key Info

| Property | Value |
|----------|-------|
| **Key** | `tbn_live_rHwyKxafnTomRS70ZjSKcYbI6IyGWyKR` |
| **Tier** | TRIAL |
| **Calls/Day** | 100 |
| **Bot Access** | 3 |
| **Expiry** | 7 days from creation |
| **Created** | May 12, 2026 |

---

## 📞 Support

- **Email**: info@hardinai.co.uk
- **Dashboard**: https://tbn.hardinai.co.uk
- **Health Check**: https://tbn.hardinai.co.uk/api/boomi/health

---

**Ready to test!** 🚀

