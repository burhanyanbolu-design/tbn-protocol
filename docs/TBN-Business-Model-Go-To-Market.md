# TBN Protocol — Business Model & Go-To-Market Strategy

**The Complete AI Governance Stack: TBN + Shango + EVIDE**

**Prepared by:** Hardin Enterprises Ltd  
**Date:** 22 May 2026  
**Version:** 1.0  

---

## 1. The Three-Layer Business Model

### The Stack

```
┌─────────────────────────────────────────────────────┐
│  EVIDE (Emanuel Celano)                             │
│  Evidentiary Reconstruction Layer                   │
│  "Can we prove WHY a decision was made?"            │
│  → Regulatory reporting, legal admissibility        │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│  SHANGO MID (Ishaan Ghosh)                          │
│  Write Governance Layer (Layers 1–8)                │
│  "Should this write be allowed?"                    │
│  → Rate limits, field control, AI reasoning, audit  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│  TBN PROTOCOL (Burhan Yanbolu)                      │
│  Trust Verification Layer (Layer 0)                 │
│  "Is this agent trusted right now?"                 │
│  → Identity, certification, cryptographic proof     │
└─────────────────────────────────────────────────────┘
```

### What Each Layer Does

| Layer | Product | Function | Output |
|-------|---------|----------|--------|
| **Layer 0** | TBN Protocol | Agent identity + trust attestation | `within_bounds: true/false` + RSA-PSS signature |
| **Layers 1–8** | Shango MID | Write governance + boundary enforcement | ALLOW/BLOCK + 8-layer decision chain |
| **Evidence** | EVIDE | Evidentiary coherence + reconstructability | Legal-grade proof of reasoning |

### Why All Three Together

A regulated enterprise needs:
1. **Proof the agent is trusted** (TBN) — for runtime control
2. **Proof the write was governed** (Shango) — for operational compliance
3. **Proof the decision is reconstructable** (EVIDE) — for regulators and courts

No single product covers all three. Together = the only complete stack.

---

## 2. Revenue Model

### Joint Product Pricing (Customer-Facing)

| Tier | Monthly | Annual | What's Included |
|------|---------|--------|-----------------|
| **POC** | £5,000 | £54,000 (10% discount) | 10K writes, 50 agents, basic audit |
| **Professional** | £12,000 | £130,000 | 100K writes, 200 agents, full audit trail |
| **Enterprise** | £25,000 | £270,000 | 1M writes, 1,000 agents, SLA, EVIDE reporting |
| **Enterprise+** | £50,000+ | Custom | Unlimited, on-prem, dedicated support, legal-grade evidence |

### Revenue Split

| Who Sells | TBN (Burhan) | Shango (Ishaan) | EVIDE (Emanuel) |
|-----------|-------------|-----------------|-----------------|
| Burhan sells | 55% | 30% | 15% |
| Ishaan sells | 30% | 55% | 15% |
| Joint sale | 40% | 40% | 20% |
| Emanuel sells | 25% | 25% | 50% |

### Annual Revenue Projections (Conservative)

| Milestone | Customers | Avg Deal | Monthly Revenue | Annual Revenue |
|-----------|-----------|----------|-----------------|----------------|
| Month 3 (first POC) | 1 | £5,000 | £5,000 | £60,000 |
| Month 6 | 3 | £10,000 | £30,000 | £360,000 |
| Month 12 | 8 | £15,000 | £120,000 | £1,440,000 |
| Month 18 | 15 | £20,000 | £300,000 | £3,600,000 |

---

## 3. Target Customer Profiles

### Ideal Customer Profile (ICP)

| Criteria | Details |
|----------|---------|
| **Size** | 500+ employees, £50M+ revenue |
| **Industry** | Financial services, insurance, healthcare, government |
| **Tech stack** | Salesforce (any cloud), using or planning AI/Agentforce |
| **Regulation** | Subject to EU AI Act, FCA, PRA, ICO, or equivalent |
| **Pain** | Deploying AI agents but can't prove governance to regulators |
| **Budget holder** | CTO, CISO, Chief Compliance Officer, Head of AI |

### Why They Buy

| Their Problem | Our Solution | Value |
|---------------|-------------|-------|
| "We can't deploy Agentforce — compliance won't sign off" | Full governance stack, real-time | Unblock AI deployment |
| "EU AI Act deadline is Dec 2027, we have no plan" | Production-ready compliance today | Avoid €7.5M–35M fines |
| "PwC charges us $950/task for manual governance" | Automated, 10K writes in 59 seconds | 90%+ cost reduction |
| "We can't prove to auditors what our AI did" | Immutable audit trail (BlackVault + EVIDE) | Audit-ready evidence |
| "Our AI made a bad write and we only found out weeks later" | Real-time interception at write boundary | Prevent damage, not just log it |

---

## 4. Go-To-Market: How to Find Customers

### Channel 1: Direct Outreach (Highest Priority)

**Target list — UK companies using Salesforce + AI:**

| Company | Why | Contact Role | Approach |
|---------|-----|-------------|----------|
| **Lloyds Banking Group** | Largest UK bank, Salesforce user, FCA regulated | Head of AI / CISO | EU AI Act compliance pitch |
| **Aviva** | Insurance, heavy Salesforce, regulated | CTO / Chief Data Officer | "Agentforce governance" |
| **Legal & General** | Insurance + asset management, Salesforce | Head of Technology | Compliance + cost saving |
| **NatWest** | Banking, AI strategy, FCA pressure | AI Programme Director | Regulatory readiness |
| **Barclays** | Investment + retail banking, Salesforce | Head of AI Governance | Enterprise+ tier |
| **AstraZeneca** | Pharma, regulated, Salesforce Health Cloud | VP Digital | Healthcare AI compliance |
| **Unilever** | Consumer goods, Salesforce, EU operations | Chief Digital Officer | EU AI Act readiness |
| **BT Group** | Telecoms, Salesforce, AI customer service | CTO | Agent governance |
| **Sage** | Accounting software, Salesforce partner | VP Engineering | ISV integration |
| **Capita** | Outsourcing, government contracts, Salesforce | Chief Technology Officer | Public sector compliance |

**Outreach template (LinkedIn DM):**

> Hi [Name], I noticed [Company] is deploying AI agents on Salesforce. We've built the first real-time governance stack that intercepts at the write boundary — not just logs after the fact. 10,000 writes governed in 59 seconds, cryptographically signed. EU AI Act Article 14 ready. Would a 15-min demo be useful? Happy to show the 10K proof.

### Channel 2: Salesforce Ecosystem

| Target | Why | Action |
|--------|-----|--------|
| **Salesforce AppExchange** | List Shango as managed package | Ishaan to build AppExchange listing |
| **Salesforce Partner Network** | Get listed as ISV partner | Apply via partner.salesforce.com |
| **Salesforce AI events** | Agentforce launch events, Dreamforce | Attend, demo, network |
| **Salesforce AEs** | Account executives who sell Agentforce | Offer as "governance add-on" they can bundle |

**Key message to Salesforce AEs:**
> "Your customer wants Agentforce but compliance is blocking it. We unblock it. You close the Agentforce deal, we close the governance deal. Everyone wins."

### Channel 3: Consulting Partners (Resellers)

| Partner | Why | Deal Structure |
|---------|-----|---------------|
| **Capgemini** | EU AI Act practice, Salesforce partner | They resell, we deliver. 70/30 split. |
| **Deloitte** | AI governance advisory | White-label our stack under their brand |
| **Accenture** | Salesforce implementation partner | Bundle governance into their projects |
| **T-Systems** | German sovereign AI, Deutsche Telekom subsidiary | Direct enterprise deal |
| **Wipro** | Salesforce practice, cost-sensitive clients | Volume play, lower price point |

**Approach:** Don't compete with consultants — **arm them**. They sell the advisory, we provide the technology. They charge £200/hour for governance consulting and use our stack to deliver it.

### Channel 4: Regulatory & Compliance Events

| Event | When | Why |
|-------|------|-----|
| **AI Safety Summit** | Various 2026 | UK government focus on AI governance |
| **EU AI Act Compliance Conference** | Q3/Q4 2026 | Direct access to compliance buyers |
| **Salesforce Dreamforce** | Sept 2026 | Largest Salesforce event globally |
| **FCA TechSprint** | Various | Financial regulator innovation programme |
| **ICO AI Auditing Framework** | Ongoing | UK data protection angle |

### Channel 5: Content & Inbound

| Content | Purpose | Frequency |
|---------|---------|-----------|
| LinkedIn posts (proof results) | Credibility + reach | 3x/week |
| "EU AI Act Countdown" series | Urgency creation | Weekly |
| Technical blog (how TBN works) | SEO + developer trust | Bi-weekly |
| Case study (when first customer lands) | Social proof | As available |
| Webinar: "Governing Agentforce" | Lead generation | Monthly |

---

## 5. Sales Process

### Stage 1: Awareness (Week 1)
- LinkedIn DM or email to target
- Share 10K proof results
- Offer 15-min demo

### Stage 2: Demo (Week 2)
- Live demo of TBN + Shango stack
- Show real-time governance in action
- Discuss their specific compliance gaps

### Stage 3: POC Proposal (Week 3)
- Propose 90-day POC at £5,000/month
- Define success criteria (e.g. "govern 10K writes with zero false positives")
- Get sign-off from compliance + tech

### Stage 4: POC Delivery (Weeks 4–12)
- Ishaan integrates Shango with their Salesforce org
- TBN provides Layer 0 verification
- Weekly reports showing governance decisions

### Stage 5: Production Contract (Week 13+)
- POC proves value → upgrade to Professional/Enterprise
- 12-month contract, annual billing
- Expand to more agents/orgs over time

---

## 6. Competitive Positioning

| Competitor | What They Do | Why We Win |
|------------|-------------|------------|
| **PwC/Deloitte** (manual) | Human governance review | We're real-time, they're after-the-fact. 100x faster, 90% cheaper. |
| **Salesforce Shield** | Encryption + event monitoring | Logging ≠ governance. We intercept, they record. |
| **OneTrust** | Privacy/compliance platform | Generic compliance, not AI-agent specific. No write interception. |
| **Fairly AI** | AI bias/fairness testing | Testing ≠ runtime governance. We operate in production. |
| **Credo AI** | AI governance platform | Policy management, not runtime enforcement. No cryptographic proof. |

**Our unique position:** We are the only stack that:
1. Operates at runtime (not just testing/auditing)
2. Intercepts at the write boundary (not just logs)
3. Provides cryptographic proof (not just reports)
4. Covers Layer 0 through Layer 8 (not just one layer)
5. Is EU AI Act Article 14 ready today (not "coming soon")

---

## 7. Immediate Actions (Next 7 Days)

| Action | Owner | Deadline |
|--------|-------|----------|
| Send partnership proposal to Ishaan | Burhan | Today (22 May) |
| Like + comment on Ishaan's LinkedIn post | Burhan | Today |
| Reply to Emanuel (EVIDE) — keep warm | Burhan | Today |
| Ishaan integrates live TBN key | Ishaan | 26 May |
| Joint 1K live proof | Both | 28 May |
| Build target list of 20 UK Salesforce enterprises | Burhan | 28 May |
| First 5 LinkedIn DMs to targets | Burhan | 30 May |
| Draft AppExchange listing copy | Ishaan | 2 June |
| 100K proof on Enterprise+ sandbox | Ishaan | 2 June |
| Joint LinkedIn announcement | Both | 5 June |

---

## 8. Key Metrics to Track

| Metric | Target (Month 1) | Target (Month 3) |
|--------|-------------------|-------------------|
| LinkedIn DMs sent | 20 | 60 |
| Demo calls booked | 5 | 15 |
| POC proposals sent | 2 | 5 |
| POC signed | 1 | 2 |
| Monthly revenue | £0 (free period) | £5,000–10,000 |

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Ishaan can't close deals (CTO-minded) | Burhan leads all commercial conversations |
| Enterprise sales cycle too long (6–12 months) | Start with mid-market (faster decision) |
| Salesforce builds native governance | We're already in production; they're 12+ months away |
| EU AI Act enforcement delayed | UK FCA + ICO still enforce independently |
| Emanuel (EVIDE) not ready | Launch with TBN + Shango first; add EVIDE later |

---

*This document is confidential to Hardin Enterprises Ltd and named partners.*
