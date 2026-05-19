# 🚀 Boomi Integration — START HERE

## What's Happening

You're integrating TBN Protocol with Boomi as trade partners. This means Boomi customers can now use TBN's trust infrastructure for AI agents directly from Boomi.

---

## What I've Done ✅

Everything is **complete and ready to go**. I've built:

1. **API Endpoints** — Three endpoints for Boomi to call
2. **Authentication** — API key system for security
3. **Documentation** — Complete guides and references
4. **Test Script** — To verify everything works
5. **Flow Diagrams** — To help you understand the flow

---

## What You Need to Do 📋

### Quick Version (5 minutes)

1. **Get API Key**
   - Go to: https://tbn.hardinai.co.uk/api/access/request
   - Choose TRIAL (free) or paid plan
   - Save your API key

2. **Configure Boomi**
   - Add HTTP connector to your process
   - URL: `https://tbn.hardinai.co.uk/api/boomi/process`
   - Header: `Authorization: Bearer tbn_live_YOUR_KEY`

3. **Test**
   - Run the test commands
   - Verify it works

4. **Deploy**
   - Activate your Boomi process
   - Done!

---

## Documentation Files 📚

Read these in order:

1. **`BOOMI-NEXT-STEPS.md`** ← Start here (quick reference)
2. **`docs/BOOMI-SETUP-GUIDE.md`** ← Detailed setup instructions
3. **`docs/BOOMI-FLOW-DIAGRAM.md`** ← Understand the flow
4. **`docs/BOOMI-INTEGRATION.md`** ← Full API reference
5. **`BOOMI-CHECKLIST.md`** ← Complete checklist
6. **`BOOMI-INTEGRATION-SUMMARY.md`** ← Full summary

---

## What Boomi Can Do

### 1. Register Bots
```json
{
  "process_type": "bot_registration",
  "data": {
    "bot_name": "MyBot",
    "bot_type": "SEARCH",
    "company": "Acme Corp",
    "email": "contact@acme.com",
    "description": "My bot"
  }
}
```

### 2. Check Certifications
```json
{
  "process_type": "certification_check",
  "data": {
    "bot_id": "tbn-bot-mybot-001",
    "cert_level": "GOLD"
  }
}
```

### 3. Query Bot Status
```json
{
  "process_type": "governance_query",
  "data": {
    "query_type": "bot_status",
    "limit": 10
  }
}
```

---

## API Response Format

All responses look like this:

**Success:**
```json
{
  "success": true,
  "process_id": "proc-12345",
  "result": { /* depends on process_type */ },
  "status": "completed"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Description of error",
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

## Quick Test

Test the health check (no auth needed):

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

---

## Files Created

- `BOOMI-NEXT-STEPS.md` — Quick action items
- `BOOMI-CHECKLIST.md` — Complete checklist
- `BOOMI-INTEGRATION-SUMMARY.md` — Full summary
- `docs/BOOMI-SETUP-GUIDE.md` — Detailed setup
- `docs/BOOMI-FLOW-DIAGRAM.md` — Flow diagrams
- `docs/BOOMI-INTEGRATION.md` — API reference (already existed)
- `demo/test_boomi_integration.py` — Test script

---

## Next Steps

1. **Read** `BOOMI-NEXT-STEPS.md` (5 min)
2. **Get** API key (5 min)
3. **Configure** Boomi (10 min)
4. **Test** (5 min)
5. **Deploy** (1 min)

**Total time: ~25 minutes**

---

## Support

- **Email:** info@hardinai.co.uk
- **Dashboard:** https://tbn.hardinai.co.uk
- **Health Check:** https://tbn.hardinai.co.uk/api/boomi/health

---

## You're Ready! 🎉

Everything is built and tested. Just follow the steps in `BOOMI-NEXT-STEPS.md` and you'll be live in 25 minutes.

**Questions?** Email info@hardinai.co.uk

