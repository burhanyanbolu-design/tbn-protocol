# Boomi Integration Setup Guide

## Status: Ready to Deploy

The TBN Protocol Boomi integration is **complete and ready to go live**. This guide tells you exactly what to do next.

---

## What You Need to Do (In Order)

### STEP 1: Get Your Boomi API Key (5 minutes)

Boomi needs an API key to authenticate with TBN. Here's how to get one:

**Option A: Get a Trial Key (Free, 7 days)**
1. Go to: https://tbn.hardinai.co.uk/api/access/request
2. Fill in:
   - Company: `Boomi` (or your company name)
   - Email: `your-email@boomi.com`
3. Click "Request Trial"
4. **Save the API key** — you'll need it in Boomi

**Option B: Get a Paid Key (Recommended for production)**
1. Go to: https://tbn.hardinai.co.uk/pricing
2. Choose a plan (STARTER £99/mo or PRO £299/mo)
3. Complete payment
4. API key will be generated automatically
5. **Save the API key**

**Your API key will look like:** `tbn_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456`

---

### STEP 2: Configure Boomi Process (10 minutes)

In your Boomi process, you need to set up the HTTP connector to call TBN.

#### 2a. Add HTTP Connector to Your Process

1. In Boomi, open your process
2. Add a new step: **HTTP Connector**
3. Configure it:
   - **Method:** `POST`
   - **URL:** `https://tbn.hardinai.co.uk/api/boomi/process`
   - **Headers:**
     ```
     Authorization: Bearer tbn_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456
     Content-Type: application/json
     ```
     (Replace with your actual API key)

#### 2b. Map Your Input Document

Transform your Boomi document to match TBN's format. Here are the three options:

**Option 1: Register a Bot**
```json
{
  "process_type": "bot_registration",
  "data": {
    "bot_name": "MySearchBot",
    "bot_type": "SEARCH",
    "company": "Acme Corp",
    "email": "contact@acme.com",
    "description": "Searches product database"
  },
  "metadata": {
    "boomi_process_id": "proc-12345",
    "timestamp": "2026-05-12T10:30:00Z",
    "source": "boomi"
  }
}
```

**Option 2: Check Bot Certification**
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

**Option 3: Query Governance Status**
```json
{
  "process_type": "governance_query",
  "data": {
    "query_type": "bot_status",
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

#### 2c. Map Your Output Document

TBN will return:
```json
{
  "success": true,
  "process_id": "proc-12345",
  "result": { /* depends on process_type */ },
  "status": "completed"
}
```

Extract the `result` field for your downstream processing.

#### 2d. Add Error Handling

Add a decision step after the HTTP call:
```
IF response.success == true
  THEN: Continue with result
  ELSE: Log error (response.error) and alert
```

---

### STEP 3: Test the Integration (5 minutes)

Before going live, test with a simple request:

**Test 1: Health Check (No Auth Required)**
```bash
curl -X GET https://tbn.hardinai.co.uk/api/boomi/health
```

Expected response:
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
      "description": "Test bot"
    },
    "metadata": {
      "boomi_process_id": "test-001",
      "timestamp": "2026-05-12T10:30:00Z",
      "source": "boomi"
    }
  }'
```

Expected response:
```json
{
  "success": true,
  "process_id": "test-001",
  "result": {
    "bot_id": "tbn-bot-testbot-001",
    "bot_name": "TestBot",
    "bot_type": "SEARCH",
    "company": "Test Corp",
    "status": "registered",
    "created_at": "2026-05-12T10:30:00Z"
  },
  "status": "completed"
}
```

---

### STEP 4: Deploy to Production (1 minute)

Once testing is complete:

1. **In Boomi:** Activate your process
2. **In TBN:** Your integration is already live at `https://tbn.hardinai.co.uk`
3. **Monitor:** Check the TBN dashboard for Boomi activity

---

## API Reference

### Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/boomi/health` | GET | No | Health check |
| `/api/boomi/process` | POST | Yes | Process handler |

### Process Types

| Type | Purpose | Use Case |
|------|---------|----------|
| `bot_registration` | Register a new bot | When Boomi customers create bots |
| `certification_check` | Verify bot certification | Before allowing bot to run |
| `governance_query` | Query bot status/violations | For compliance & monitoring |

### Error Responses

If something goes wrong, TBN returns:
```json
{
  "success": false,
  "error": "Description of what went wrong",
  "status": "error"
}
```

Common errors:
- `process_type is required` — Add `process_type` field
- `Unknown process_type: xxx` — Use valid type
- `bot_id is required` — Add `bot_id` field
- `Bot not found: xxx` — Check bot_id is correct
- `Invalid bot_type: xxx` — Use: SEARCH, VALIDATOR, CONNECTOR, MESSENGER

---

## Subscription Tiers

| Tier | Price | Calls/Day | Bots | Features |
|------|-------|-----------|------|----------|
| TRIAL | Free | 100 | 3 | Read-only, 7 days |
| STARTER | £99/mo | 1,000 | 10 | Read-only, sports/financial data |
| PRO | £299/mo | 10,000 | All | Read-write, real-time, webhooks |
| ENTERPRISE | Custom | Unlimited | All | Dedicated support, SLA |

---

## Support

- **Email:** info@hardinai.co.uk
- **Dashboard:** https://tbn.hardinai.co.uk
- **GitHub:** https://github.com/burhanyanbolu-design/tbn-protocol
- **Status:** https://tbn.hardinai.co.uk/api/boomi/health

---

## Checklist

- [ ] Get API key (Step 1)
- [ ] Configure HTTP connector in Boomi (Step 2a)
- [ ] Map input document (Step 2b)
- [ ] Map output document (Step 2c)
- [ ] Add error handling (Step 2d)
- [ ] Test health check (Step 3)
- [ ] Test bot registration (Step 3)
- [ ] Deploy to production (Step 4)
- [ ] Monitor Boomi activity

---

## Next Steps

1. **Get your API key** — Go to https://tbn.hardinai.co.uk/api/access/request
2. **Configure Boomi** — Follow Step 2 above
3. **Test** — Run the test commands in Step 3
4. **Deploy** — Activate your process in Boomi
5. **Monitor** — Check the TBN dashboard

**Questions?** Email info@hardinai.co.uk

