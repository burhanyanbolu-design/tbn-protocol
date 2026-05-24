# TBN Protocol — Registration & Verification Security Spec

## How Customers Register Agents (Product Design)

**Date:** 24 May 2026  
**Status:** Design — to be built  

---

## Registration Flow

1. Customer goes to tbn.hardinai.co.uk/customer
2. Enters company email (must be company domain, not Gmail/Yahoo)
3. TBN sends email verification link → customer clicks it
4. Customer enters agent details:
   - Agent name
   - Agent URL (must be HTTPS)
   - What the agent does (purpose/scope)
   - Agent type
   - Company registration number (optional for international)
5. TBN runs automated checks
6. If all pass → CERTIFIED
7. If any fail → REJECTED with reason

---

## Automated Verification Checks

| # | Check | What it proves | Required? |
|---|-------|---------------|-----------|
| 1 | **Email verification** | They own that email address | ✅ Always |
| 2 | **Domain match** | Email domain = agent URL domain | ✅ Always |
| 3 | **SSL check** | Agent URL has valid HTTPS certificate | ✅ Always |
| 4 | **Company number** | Legal entity exists (Companies House / OpenCorporates) | 🟡 Optional (higher trust) |

### Rules:
- Gmail, Yahoo, Hotmail, etc. → REJECTED ("Use your company email")
- Agent URL without HTTPS → REJECTED ("Agent must be on a secure domain")
- Email domain ≠ agent URL domain → REJECTED ("Email must match agent domain")
- All checks pass → CERTIFIED

---

## Why This Works

- **SSL certificate** already proves domain ownership (piggybacking on existing trust)
- **Email verification** proves the person has access to that company's email
- **Domain match** ties the agent to the company — can't register someone else's agent
- **Company number** (when provided) confirms legal entity via public registry

---

## International Support

| Country | Company Registry | How to check |
|---------|-----------------|-------------|
| UK | Companies House | Free API |
| US | State registries | OpenCorporates |
| EU | National registries | OpenCorporates |
| India | MCA / UDYAM | OpenCorporates |
| Global | OpenCorporates.com | Aggregates 200+ countries |

For international companies without company numbers: rely on email + domain + SSL (3 checks still strong).

---

## Trust Levels Based on Verification

| Level | Checks Passed | Badge | Access |
|-------|--------------|-------|--------|
| L1 — Basic | Email verified only | ⚪ | Trial access |
| L2 — Verified | Email + domain + SSL | 🔵 | Standard access |
| L3 — Business | Email + domain + SSL + company number | 🟢 | Full access |
| L4 — Enterprise | All above + contract + SLA | 🟡 | Enterprise features |
| L5 — Critical | All above + KYC + government verification | 🔴 | CNI/regulated access |

---

## What TBN Stores Per Agent

- Agent ID (tbn-bot-xxxxx)
- Agent name
- Agent URL
- Declared purpose/scope
- Company name
- Company email (verified)
- Company registration number (if provided)
- Registration date
- Certification level
- SSL certificate status at registration
- All verification events (immutable log)

---

## Key Principles

1. **TBN verifies identity — not behaviour** (that's Shango's job)
2. **Registration must be tight** — because TBN's certificate is only as trustworthy as the registration process
3. **Start simple, add checks over time** — don't scare early customers away
4. **Use existing trust infrastructure** (SSL) rather than building from scratch
5. **No Gmail/Yahoo** — company email only for business accounts
6. **Immutable record** — once registered, the history can't be changed

---

## Future Parameters to Add

- IP address logging at registration
- Geographic location verification
- Multi-factor authentication for account access
- Agent behaviour monitoring (post-registration)
- Automatic SSL expiry monitoring
- Domain ownership re-verification (annual)
- Partner referral verification (existing partners vouch for new ones)
