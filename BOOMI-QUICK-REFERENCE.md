# Boomi Integration — Quick Reference Card

## 🚀 Get Started in 4 Steps

### Step 1: Get API Key (5 min)
```
Go to: https://tbn.hardinai.co.uk/api/access/request
Choose: TRIAL (free) or paid plan
Save: Your API key (tbn_live_xxx)
```

### Step 2: Configure Boomi (10 min)
```
URL: https://tbn.hardinai.co.uk/api/boomi/process
Header: Authorization: Bearer tbn_live_YOUR_KEY
Header: Content-Type: application/json
```

### Step 3: Test (5 min)
```bash
curl -X GET https://tbn.hardinai.co.uk/api/boomi/health
```

### Step 4: Deploy (1 min)
```
Activate your Boomi process
Done!
```

---

## 📋 Three Request Types

### Type 1: Register Bot
```json
{
  "process_type": "bot_registration",
  "data": {
    "bot_name": "MyBot",
    "bot_type": "SEARCH",
    "company": "Acme Corp",
    "email": "contact@acme.com",
    "description": "My bot"
  },
  "metadata": {
    "boomi_process_id": "proc-12345",
    "timestamp": "2026-05-12T10:30:00Z",
    "source": "boomi"
  }
}
```

### Type 2: Check Certification
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

### Type 3: Query Status
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

## ✅ Response Format

### Success
```json
{
  "success": true,
  "process_id": "proc-12345",
  "result": { /* depends on type */ },
  "status": "completed"
}
```

### Error
```json
{
  "success": false,
  "error": "Description",
  "status": "error"
}
```

---

## 💰 Pricing

| Tier | Price | Calls/Day |
|------|-------|-----------|
| TRIAL | Free | 100 |
| STARTER | £99/mo | 1,000 |
| PRO | £299/mo | 10,000 |
| ENTERPRISE | Custom | Unlimited |

---

## 🔗 Links

- **API Key Request:** https://tbn.hardinai.co.uk/api/access/request
- **Health Check:** https://tbn.hardinai.co.uk/api/boomi/health
- **Dashboard:** https://tbn.hardinai.co.uk
- **Email:** info@hardinai.co.uk

---

## 📚 Documentation

- `START-HERE-BOOMI.md` — Quick overview
- `BOOMI-NEXT-STEPS.md` — Action items
- `docs/BOOMI-SETUP-GUIDE.md` — Detailed setup
- `docs/BOOMI-FLOW-DIAGRAM.md` — Flow diagrams
- `BOOMI-CHECKLIST.md` — Complete checklist

---

## ⏱️ Timeline

- **5 min:** Get API key
- **10 min:** Configure Boomi
- **5 min:** Test
- **1 min:** Deploy
- **Total: 21 minutes**

---

## 🎯 Success Criteria

✅ Health check returns `{"status": "healthy"}`
✅ Bot registration returns `{"success": true}`
✅ Certification check returns `{"success": true}`
✅ Governance query returns `{"success": true}`
✅ Boomi process completes without errors

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| 404 error | Check URL is correct |
| 401 error | Check API key is correct |
| 400 error | Check request format is valid |
| Timeout | Check network connection |
| Rate limit | Upgrade subscription tier |

---

## 📞 Support

**Email:** info@hardinai.co.uk

**Questions?** Email support with:
- Your API key (first 20 chars only)
- The request you sent
- The error you received
- Your subscription tier

---

## ✨ You're Ready!

Everything is built and tested. Just follow the 4 steps above.

**Start with:** `START-HERE-BOOMI.md`

