# Boomi Integration — What You Need to Do Next

## Status: ✅ READY TO DEPLOY

The Boomi integration is **complete and ready to go live**. Here's exactly what you need to do.

---

## Your Action Items (In Order)

### 1️⃣ Get Your API Key (5 minutes)

Boomi needs an API key to authenticate with TBN.

**Go to:** https://tbn.hardinai.co.uk/api/access/request

Fill in:
- Company: `Boomi` (or your company name)
- Email: `your-email@boomi.com`

Click "Request Trial" (free, 7 days) or go to pricing for a paid plan.

**Save your API key** — it looks like: `tbn_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456`

---

### 2️⃣ Configure Boomi Process (10 minutes)

In your Boomi process, add an HTTP connector:

**URL:** `https://tbn.hardinai.co.uk/api/boomi/process`

**Headers:**
```
Authorization: Bearer tbn_live_YOUR_KEY_HERE
Content-Type: application/json
```

**Send one of these three types of requests:**

**A) Register a Bot**
```json
{
  "process_type": "bot_registration",
  "data": {
    "bot_name": "MyBot",
    "bot_type": "SEARCH",
    "company": "Acme Corp",
    "email": "contact@acme.com",
    "description": "My bot description"
  },
  "metadata": {
    "boomi_process_id": "proc-12345",
    "timestamp": "2026-05-12T10:30:00Z",
    "source": "boomi"
  }
}
```

**B) Check Bot Certification**
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

**C) Query Bot Status**
```json
{
  "process_type": "governance_query",
  "data": {
    "query_type": "bot_status",
    "limit": 10
  },
  "metadata": {
    "boomi_process_id": "proc-12347",
    "timestamp": "2026-05-12T10:40:00Z",
    "source": "boomi"
  }
}
```

---

### 3️⃣ Test It (5 minutes)

**Test 1: Health Check (No Auth)**
```bash
curl -X GET https://tbn.hardinai.co.uk/api/boomi/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "TBN Protocol",
  "version": "1.0.0",
  "boomi_integration": "enabled",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

**Test 2: Register a Bot (With Auth)**
```bash
curl -X POST https://tbn.hardinai.co.uk/api/boomi/process \
  -H "Authorization: Bearer tbn_live_YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "process_type": "bot_registration",
    "data": {
      "bot_name": "TestBot",
      "bot_type": "SEARCH",
      "company": "Test Corp",
      "email": "test@test.com",
      "description": "Test"
    },
    "metadata": {
      "boomi_process_id": "test-001",
      "timestamp": "2026-05-12T10:30:00Z",
      "source": "boomi"
    }
  }'
```

Should return:
```json
{
  "success": true,
  "process_id": "test-001",
  "result": {
    "bot_id": "tbn-bot-testbot-001",
    "bot_name": "TestBot",
    "status": "registered"
  },
  "status": "completed"
}
```

---

### 4️⃣ Deploy to Production (1 minute)

1. Activate your Boomi process
2. TBN is already live at `https://tbn.hardinai.co.uk`
3. Done!

---

## What TBN Returns

All responses follow this format:

**Success:**
```json
{
  "success": true,
  "process_id": "your-process-id",
  "result": { /* depends on process_type */ },
  "status": "completed"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Description of what went wrong",
  "status": "error"
}
```

---

## Pricing

| Tier | Price | Calls/Day | Features |
|------|-------|-----------|----------|
| TRIAL | Free | 100 | 7 days, read-only |
| STARTER | £99/mo | 1,000 | Read-only |
| PRO | £299/mo | 10,000 | Read-write, real-time |
| ENTERPRISE | Custom | Unlimited | Dedicated support |

---

## Documentation

- **Full Setup Guide:** `docs/BOOMI-SETUP-GUIDE.md`
- **API Reference:** `docs/BOOMI-INTEGRATION.md`
- **Test Script:** `demo/test_boomi_integration.py`

---

## Support

- **Email:** info@hardinai.co.uk
- **Dashboard:** https://tbn.hardinai.co.uk
- **Health Check:** https://tbn.hardinai.co.uk/api/boomi/health

---

## Quick Checklist

- [ ] Get API key from https://tbn.hardinai.co.uk/api/access/request
- [ ] Add HTTP connector to Boomi process
- [ ] Set URL to `https://tbn.hardinai.co.uk/api/boomi/process`
- [ ] Add Authorization header with your API key
- [ ] Map your input document (choose A, B, or C above)
- [ ] Test health check endpoint
- [ ] Test bot registration endpoint
- [ ] Activate Boomi process
- [ ] Monitor activity on TBN dashboard

---

## That's It!

You're ready to go. Start with Step 1 (get your API key), then follow Steps 2-4.

**Questions?** Email info@hardinai.co.uk

