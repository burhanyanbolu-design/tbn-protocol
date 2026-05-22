# YC Application Update — TBN Protocol

**Company:** Hardin Enterprises Ltd (trading as Hardin AI Solutions)  
**Product:** TBN Protocol — Trust infrastructure for AI agents  
**Batch:** YC Summer 2026  
**Date:** 22 May 2026  

---

## What's Changed Since We Applied

Companies are finding us and asking to use TBN as their protocol layer. We didn't go looking for them — they came to us.

In the last 2 weeks, 5 independent companies have integrated or begun integrating TBN as their Layer 0 trust infrastructure:

| Partner | What They Do | How They Use TBN | Status |
|---------|-------------|-----------------|--------|
| **Shango** (India/UK) | AI write governance for Salesforce | Layer 0 — verifies every agent before it writes to CRM | Live integration, 10K record proof completed |
| **DigiEmu** (Switzerland) | AI agent interoperability | Layer 0 — cross-boundary trust verification | Live in production, RSA-PSS signature verified |
| **EVIDE** (Italy) | Evidentiary AI compliance | Layer 0 — cryptographic anchor for legal evidence chains | Architecture alignment in progress |
| **CLARIXO** (Asia) | Trust-state evidence platform | Layer 0 — verify endpoint as trust-state proof | Approved partner, active |
| **Constitutional Memory / BlackVault** (Spain) | AI governance middleware | Layer 0 — immutable audit anchoring | Integration via Shango partnership |

**None of these companies are paying us yet.** But all of them need us, and the first commercial deal is being negotiated now.

---

## The Shango Partnership — Our First Revenue Path

### What Shango Does
Shango (founded by Ishaan Ghosh, ex-PwC 6yr, ex-Accenture 3yr) governs AI agent writes to Salesforce. Their system has 8 governance layers that decide whether an AI agent's write should be allowed or blocked.

### What TBN Does For Them
TBN is Layer 0 — the first check. Before Shango's 8 layers even run, TBN cryptographically verifies: "Is this agent trusted?" If not, the write is blocked immediately.

### The Proof (22 May 2026)
```
10,000 AI writes evaluated in 59 seconds
├── 390 BLOCKED by governance
└── 9,610 ALLOWED
    └── TBN Layer 0 latency: 0.059ms per attestation
    └── 170,813 immutable audit entries created
    └── Every decision cryptographically signed (RSA-PSS-SHA256)
```

### Why This Matters Commercially
- PwC charges ~$9,500 for 10 manual governance tasks ($950/task)
- Shango + TBN does 10,000 governance decisions in 59 seconds
- EU AI Act fines: up to €35M or 7% of global turnover for non-compliance
- Deadline: December 2027

### Proposed Pricing
| Tier | Monthly | Target |
|------|---------|--------|
| POC | £5,000 | Mid-market first engagement |
| Professional | £12,000 | Enterprise departments |
| Enterprise | £25,000 | Large regulated companies |
| Enterprise+ | £50,000+ | Banks, insurers, government |

### Revenue Split
Whoever brings the customer takes 55–60%. The delivery partner takes 30%. This incentivises both sides to sell.

---

## Why Companies Keep Finding Us

TBN is **protocol-level infrastructure** — like HTTPS or DNS but for AI trust. It's not an application. It's the layer that applications build on.

Every company building AI governance, AI compliance, or AI interoperability needs a trust anchor. That's us. We don't compete with any of our partners — we're the foundation they all need.

**The pattern we're seeing:**
1. Company builds AI product
2. Their customers ask: "How do I know your AI is trustworthy?"
3. Company finds TBN — the only open protocol that provides cryptographic trust verification
4. They integrate TBN as Layer 0
5. Now their product has verifiable trust built in

This is a **network effect**. Every new partner makes TBN more valuable to the next one.

---

## Traction Summary

| Metric | Value |
|--------|-------|
| Partners integrated/integrating | 5 |
| Countries represented | 5 (UK, India, Switzerland, Italy, Spain) |
| Live production proof | 10,000 records, 59 seconds |
| API latency | 0.059ms (cached), 234ms (batch 1,000 agents) |
| Throughput | 4,273 agents/sec verification rate |
| Audit entries generated | 170,813+ |
| Revenue | £0 (pre-revenue, first deal in negotiation) |
| First commercial deal expected | June 2026 |
| PyPI package published | tbn-protocol v0.1.0 (May 2026) |
| GitHub | Public, AGPL-3.0 |

---

## What We Need From YC

1. **$500K investment** — to hire Ishaan full-time as technical delivery lead and fund first 6 months of enterprise sales
2. **Network** — introductions to Salesforce, enterprise AI buyers, and EU compliance teams
3. **Credibility** — "YC-backed" opens doors at enterprise level that a solo founder can't
4. **Speed** — we have the product and the partners. We need to close the first 3 paying customers before the EU AI Act deadline creates a rush and bigger players enter

---

## Team

| Name | Role | Background |
|------|------|-----------|
| **Burhan Yanbolu** | CEO, Founder | Full-stack engineer, built 5 AI products, Hardin AI Search (143 users) |
| **Ishaan Ghosh** | Technical Partner (Shango) | Ex-PwC (6yr), Ex-Accenture (3yr), Ex-IBM (1yr). Built 8-layer governance system |
| **Cem Aslan** | Automation Director | Enterprise automation specialist |
| **Sukumar Srinivasan** | Cloud Services Director | Cloud infrastructure and DevOps |

---

## Demo

- **Live dashboard:** https://tbn.hardinai.co.uk
- **Video demo:** https://drive.google.com/file/d/1SfLMFRSgrhx1lHDQc-pKDOCtI5LsH3Y8/view
- **Shango 10K proof:** Available on request
- **PyPI:** https://pypi.org/project/tbn-protocol/0.1.0/

---

*Hardin Enterprises Ltd — Building the trust layer for AI agents.*
