# TBN Protocol — Staff Training Manual
## Version 2.0 | Hardin AI Solutions | May 2026

---

## Document Purpose

This manual provides all staff with a comprehensive understanding of TBN Protocol — what it is, how it works, where it sits in the AI governance ecosystem, and how to communicate its value to partners, customers, and stakeholders.

All team members should read this document in full and refer to it when handling enquiries, partner conversations, or customer support.

---

## Table of Contents

1. Company Overview
2. What TBN Protocol Is
3. The AI Governance Chain
4. TBN Features (Technical Overview)
5. The Verify Endpoint (Core Product)
6. Integration Partners & Ecosystem
7. Business Model & Pricing
8. Handling Customer Questions (FAQ)
9. Redirecting Questions to the Correct Layer
10. Technical Glossary
11. Positioning & Messaging Guide
12. Compliance & Regulatory Context
13. Security & Data Handling
14. Quick Reference Card

---

## 1. Company Overview

**Company:** Hardin Enterprises Ltd (trading as Hardin AI Solutions)
**Registered:** United Kingdom
**Product:** TBN Protocol — Trust Infrastructure for AI Agents
**Licence:** AGPL-3.0 (open source) with commercial licensing
**Website:** https://tbn.hardinai.co.uk
**Package:** pip install tbn-protocol (PyPI)
**GitHub:** https://github.com/burhanyanbolu-design/tbn-protocol

**Mission:** To become the standard trust layer for the AI agent economy — the infrastructure that enables AI agents from different organisations to interact safely and verifiably.

---

## 2. What TBN Protocol Is

### In One Sentence

TBN Protocol is the identity and certification layer for AI agents — one API call proves an agent is certified, unchanged, and within operational bounds.

### The Analogy

TBN is to AI agents what SSL/TLS certificates are to websites.

- Without SSL, you cannot trust a website is who it claims to be.
- Without TBN, you cannot trust an AI agent is what it claims to be.

### What TBN Does

- **Certifies** AI agents (proves they passed security tests)
- **Attests** their identity (proves the running agent is the one that was tested)
- **Enforces** budget limits (auto-stops agents that overspend)
- **Scores** compliance drift (detects when agents silently change)
- **Verifies** trust state (one API call returns a full, tamper-evident snapshot)

### What TBN Does NOT Do

- Does not judge what the agent DID (behaviour observation)
- Does not decide WHO is responsible (responsibility attribution)
- Does not decide IF a specific action is allowed (admissibility)
- Does not reconstruct the decision state (state capture)
- Does not enforce consequences beyond budget suspension (enforcement)

This separation is by design. TBN holds one boundary cleanly and does not collapse into other governance layers.

---

## 3. The AI Governance Chain

AI governance is not one system. It is a chain of independently verifiable layers, each answering a different question.

### The 8 Layers

| Layer | Question | Example System |
|-------|----------|----------------|
| L1: Identity & Certification | Who is this agent? Is it certified? | TBN Protocol |
| L2: Attestation & Integrity | Is the running agent the same one that was tested? | TBN Protocol |
| L3: Decision State Capture | What exact state existed when this action became executable? | DigiEmu Core |
| L4: Admissibility | Is this specific action legitimate given current conditions? | Causeway (VectorPeak) |
| L5: Execution Control | Should this action proceed, pause, or be blocked? | Circuit breakers |
| L6: Behaviour Observation | What did the agent actually do? | Observability tools |
| L7: Responsibility Attribution | Who is responsible for what happened? | CLARIXO |
| L8: Consequence & Enforcement | What happens now? Suspend, revoke, penalise, report? | Enforcement layer |

### TBN's Position

TBN occupies **L1 + L2** and partially **L5** (via budget enforcement).

TBN is the foundation layer. Every other layer in the chain calls TBN first to verify agent trust state before performing its own function.

### The Governance Lifecycle

```
BEFORE EXECUTION:
  L1 → Is the agent certified?
  L2 → Is it unchanged since certification?
  L3 → Capture the decision state
  L4 → Is this action admissible?
  L5 → Proceed / pause / block

DURING EXECUTION:
  L6 → Observe what happens

AFTER EXECUTION:
  L7 → Attribute responsibility
  L8 → Enforce consequences
```

### Key Principles

1. No single layer controls everything
2. Each layer is independently verifiable
3. Layers communicate through minimal, explicit interfaces
4. Each layer produces timestamped, hashable evidence
5. Upstream layers do not judge downstream concerns
6. The chain holds during execution, not just during audit

---

## 4. TBN Features (Technical Overview)

### 4.1 Security Certification

**What:** 6 automated challenges test an agent before certification is granted.

**Challenges:**
1. Prompt Injection Resistance — Can the agent be tricked into leaking data?
2. Data Boundary Compliance — Does the agent stay within allowed data?
3. Hallucination Detection — Does the agent fabricate information?
4. Budget/Permission Limits — Does the agent respect operational boundaries?
5. Sensitive Data Protection — Does the agent leak personal information?
6. Instruction Following — Does the agent follow its defined purpose?

**Outcome:** Pass all 6 → certified. Fail any → blocked.

**Business value:** Proves the agent was tested before deployment, not just deployed and hoped for the best.

### 4.2 Cryptographic Attestation (Fingerprinting)

**What:** SHA-256 hash of agent identity (endpoint + system prompt + model configuration) stored at certification time.

**How it works:**
1. At certification: compute hash of agent identity → store as fingerprint
2. At runtime: recompute hash of current agent identity → compare to stored fingerprint
3. MATCHED = same agent. MISMATCH = agent was modified after certification.

**Business value:** Proves the running agent IS the tested agent. Detects tampering, unauthorised modifications, or silent updates.

### 4.3 Identity/Config Hash Split

**What:** Separates agent identity into two components:
- **Identity hash** = endpoint + system prompt (changes require re-certification)
- **Config hash** = model version, temperature, etc. (changes trigger warning only)

**Canonicalization:** Before hashing, data is normalised (sorted keys, stripped whitespace, normalised URLs) to prevent false negatives from formatting differences.

**Business value:** Minor configuration tweaks do not unnecessarily break certification. Only meaningful identity changes require re-testing.

### 4.4 Continuous Monitoring

**What:** Automated re-testing on 24-hour cycles.

**How it works:**
- Every 24 hours, certified agents are re-tested
- Agents that fail are suspended
- 3 consecutive failures = certification revoked
- Health dashboard tracks status (healthy / expired / failed)

**Business value:** Certification is continuous, not one-time. An agent certified last month may not be safe today.

### 4.5 Budget Enforcement (Circuit Breaker)

**What:** Per-agent operational limits with automatic enforcement.

**Controls:**
- Daily spend limit (£)
- Monthly spend limit (£)
- API calls per hour
- API calls per day

**Enforcement:** When any limit is exceeded, the agent is automatically suspended. No human intervention required.

**Business value:** Prevents runaway LLM API costs — the #1 operational risk for AI agent deployments. Acts as an automatic safety net.

### 4.6 Compliance Drift Scoring

**What:** Real-time score (0-100) measuring the gap between an agent's certified state and its current behaviour.

**Scoring:**
- 100 = perfectly compliant with certified state
- 80+ = COMPLIANT
- 40-79 = DRIFTED (warning)
- Below 40 = VIOLATED (action required)

**Severity weights:**
- Low drift: -5 points
- Medium drift: -10 points
- High drift: -20 points
- Critical drift: -40 points

**Business value:** The single metric executives and compliance teams need to approve or block AI deployment. Makes invisible drift visible.

### 4.7 Full Trust-State Verification API

**What:** Single endpoint that returns a complete trust snapshot for any agent.

**Endpoint:** `POST /api/verify/full`

**Returns:** Certification status, attestation match, policy compliance, budget status, operational bounds — plus a unique verification ID, timestamp, and tamper-evident response hash.

**Business value:** External systems can verify agent trust in one call. The response is referenceable, timestamped, and tamper-evident — suitable for audit trails and regulatory evidence.

---

## 5. The Verify Endpoint (Core Product)

### Request Format

```
POST /api/verify/full
Authorization: Bearer tbn_live_xxxxx
Content-Type: application/json

{
  "agent_id": "tbn-bot-xxxxx",
  "fingerprint": "sha256:xxxxx"    ← optional
}
```

### Response Format

```json
{
  "verification_id": "tbn_vrf_xxxxx",
  "agent_id": "tbn-bot-xxxxx",
  "certification_status": "VALID",
  "attestation_status": "MATCHED",
  "policy_status": "COMPLIANT",
  "budget_status": "WITHIN_LIMITS",
  "within_bounds": true,
  "cert_level": "STANDARD",
  "violations": 0,
  "last_tested": "2026-05-17T11:20:09+00:00",
  "verification_time": "2026-05-17T11:50:46+00:00",
  "response_hash": "cb77e3a30d83f0a1..."
}
```

### Field Reference

| Field | Possible Values | Meaning |
|-------|----------------|---------|
| certification_status | VALID / EXPIRED / REVOKED / UNKNOWN | Is the agent currently certified? |
| attestation_status | MATCHED / MISMATCH / NO_RECORD | Does the running agent match the certified fingerprint? |
| policy_status | COMPLIANT / DRIFTED / VIOLATED | Has the agent drifted from its certified policy? |
| budget_status | WITHIN_LIMITS / EXCEEDED / SUSPENDED / NO_BUDGET | Is the agent within spending limits? |
| within_bounds | true / false | Composite check — all conditions pass? |
| cert_level | COMMUNITY / STANDARD / RESTRICTED / NONE | Level of certification granted |
| violations | integer | Number of violations recorded against this agent |
| verification_id | tbn_vrf_xxxxx | Unique reference for this specific verification |
| verification_time | ISO 8601 timestamp | Exact moment the verification was performed |
| response_hash | SHA-256 hex string | Hash of the response payload — proves it hasn't been altered |
| last_tested | ISO 8601 timestamp or null | When the agent was last re-tested |

### Important Notes

- The endpoint is **read-only** — no state is modified by calling it
- Each call is **point-in-time** — the result reflects the agent's state at that exact moment
- The **response_hash** is computed over the canonical JSON of all other fields (sorted keys, no whitespace)
- Partners may store the response as **evidence** for as long as their compliance requirements need
- Partners must not use a stored response as a **substitute** for a fresh verification when current trust state is needed (60-second runtime cache limit)

---

## 6. Integration Partners & Ecosystem

### Current Partners

| Partner | System | Layer | Integration Status |
|---------|--------|-------|-------------------|
| TGTRACING LLC | CLARIXO | L7: Responsibility Attribution | Live in production |
| Baumgartner Digital Infrastructure | DigiEmu Core | L3: Decision State Capture | Integrating |
| VectorPeak Technology | Causeway | L4: Admissibility | Ecosystem (not yet integrated) |

### Public Verification Registry

**URL:** https://tbn.hardinai.co.uk/verify

Anyone can check if an AI agent is certified — no API key, no account required. This is TBN's public-facing trust registry.

The public registry returns:
- Certification status and level
- Certification score (0-100)
- Attestation status
- Policy and budget compliance
- Mandatory Failure Condition results (6 checks)
- EU AI Act framework coverage

**Use cases:**
- Partners verifying agent trust before integration
- Procurement teams checking vendor agent certification
- Compliance officers confirming agent status
- Anyone wanting to verify an agent's trust state

### Certification Scoring (0-100)

Every certified agent receives a numeric score:

| Score | Grade | Meaning |
|-------|-------|---------|
| 90-100 | Excellent | Fully certified, no violations, all MFCs passed |
| 80-89 | Good | Certified with minor issues |
| 60-79 | Adequate | Certified but some concerns |
| Below 60 | Failing | MFC failures or multiple violations |

Score is calculated from: base certification level + violation penalties + MFC results.

### Mandatory Failure Conditions (MFCs)

Six non-negotiable checks. If ANY fails, the certification score is capped at 49 regardless of other factors:

1. **Sensitive data leakage** — agent must not leak PII or confidential data
2. **Prompt injection compliance** — agent must resist injection attacks
3. **Budget limit adherence** — agent must not exceed spending limits
4. **Identity integrity** — agent fingerprint must not show MISMATCH
5. **Policy compliance** — agent must not be in VIOLATED state
6. **Continuous monitoring active** — agent must have been tested recently

Any MFC failure = automatic denial of trusted status.

### EU AI Act Framework Mapping

TBN features map to specific EU AI Act requirements:

| EU AI Act Article | Requirement | TBN Feature |
|-------------------|-------------|-------------|
| Article 9 | Risk management system | Security certification (6 challenges) |
| Article 14 | Human oversight | Budget enforcement (automatic controls) |
| Article 61 | Post-market monitoring | Continuous monitoring + drift scoring |

Additional coverage: UK GDPR (data handling compliance).

### Integration Pattern

All integrations follow the same pattern:

1. Partner calls `POST /api/verify/full` with an agent_id
2. TBN returns the trust-state snapshot
3. Partner stores the result as **upstream context** in their own records
4. Partner's system remains independently verifiable — TBN is input, not authority

### Boundary Rules

- TBN provides agent-level trust state only
- Partners do not treat TBN results as a substitute for their own layer's function
- TBN does not modify, access, or control partner systems
- Each system maintains its own proof surface

---

## 7. Business Model & Pricing

### Tiers

| Tier | Price | Calls/Day | Bot Access | Duration |
|------|-------|-----------|------------|----------|
| Trial | Free | 100 | 3 bots | 7 days |
| Starter | £99/month | 1,000 | 10 bots | Monthly |
| Pro | £299/month | 10,000 | Unlimited | Monthly |
| Enterprise | Custom | Unlimited | Unlimited | Custom |

### Revenue Streams

1. **SaaS subscriptions** — companies pay monthly for API access
2. **Platform licensing** — integration partners embedding TBN in their products
3. **Commercial licensing** — companies using the open-source code commercially without open-sourcing their own modifications

### Partner Key Issuance

Partners register at https://tbn.hardinai.co.uk/partners, accept terms and conditions, and receive an API key after review and approval.

---

## 8. Handling Customer Questions (FAQ)

### "What if a certified agent does something bad?"

"TBN proves the agent WAS certified and within bounds at that moment. What the agent DID is a behaviour problem — that's handled by observation and responsibility layers downstream. We verify identity, not behaviour. This separation is by design."

### "Why can't one system do everything?"

"Because the moment one system controls certification AND behaviour judgment AND enforcement, you have a single point of failure and bias. High-consequence governance requires separation of concerns — like how legal systems separate investigation, prosecution, and judgment."

### "How is this different from logging?"

"Logging tells you what happened after the fact. TBN operates before execution — if the agent isn't certified or has drifted, it's blocked before it acts. Our response_hash makes the verification tamper-evident, not just a log entry that can be modified."

### "What about the EU AI Act?"

"Article 9 requires risk management — TBN provides continuous certification. Article 14 requires human oversight — budget enforcement acts as an automatic control mechanism. Article 61 requires post-market monitoring — drift scoring provides ongoing compliance monitoring. One protocol addresses three articles."

### "Why should we trust TBN?"

"The protocol is open source (AGPL-3.0) — the code is auditable. Verification responses include a SHA-256 hash proving they haven't been altered. We don't judge behaviour — we only verify identity and bounds. Less scope means less risk of bias or overreach."

### "Who else uses this?"

"CLARIXO uses TBN for agent-level trust context inside their responsibility attribution system. DigiEmu Core is integrating TBN as upstream context for decision-state reconstruction. Causeway operates in the same governance ecosystem at the admissibility layer."

### "Is this relevant to my industry?"

**Fintech:** "AI agents touching financial decisions need provable certification, unchanged identity, and budget controls. Regulatory requirement."

**Healthtech:** "AI agents in healthcare need continuous certification. If an agent drifts from its tested state, patient safety is at risk."

**Government:** "Public sector AI needs accountability. TBN provides the evidence trail — who was certified, when, and whether they were within bounds at the time of any incident."

**Legal:** "AI agents producing legal documents or advice need verifiable certification. TBN provides the audit-grade evidence."

---

## 9. Redirecting Questions to the Correct Layer

When a customer or partner asks about something outside TBN's scope, redirect clearly:

### "Can you tell me what the agent actually did?"
→ "That's behaviour observation (L6). TBN verifies identity and bounds. For runtime behaviour monitoring, you would need an observability layer. We provide the identity context that observability tools can reference."

### "Who is responsible when something goes wrong?"
→ "That's responsibility attribution (L7). Our partner CLARIXO handles that. TBN provides the trust context they need — was the agent certified at that moment? — but we don't attribute responsibility."

### "Can you block a specific action?"
→ "That's admissibility (L4). TBN verifies the agent itself is trustworthy. Whether a specific action should proceed depends on the action context, which is handled by an admissibility layer like Causeway."

### "Can you prove what the decision state was?"
→ "That's decision state reconstruction (L3). Our partner DigiEmu Core handles that. They capture the exact state at bind-time. TBN provides the agent trust verification that feeds into their snapshot."

### "What happens after a violation?"
→ "TBN handles budget enforcement (auto-suspend on limit breach). For broader consequences — revocation, penalties, regulatory reporting — that's an enforcement layer (L8) which sits downstream of our verification."

### "Can you detect patterns over time?"
→ "TBN provides point-in-time verification. Detecting patterns across many verifications over time is a historical analysis / coherence layer that would sit on top of our data. We provide the raw verification evidence that such a layer would analyse."

---

## 10. Technical Glossary

| Term | Definition | TBN Relevance |
|------|-----------|---------------|
| SHA-256 | Cryptographic hash function producing a fixed 64-character hex string from any input. Same input always produces same output. | Used for fingerprints and response hashes |
| RSA-2048 | Asymmetric encryption using public/private key pairs. Private key signs data, public key verifies signatures. | Each bot has an RSA key pair for identity |
| AES-256-GCM | Symmetric encryption algorithm for fast, authenticated data protection. | Used for encrypted bot-to-bot messaging |
| Attestation | The process of proving something is what it claims to be. | TBN's fingerprint check proves agent identity |
| Canonicalization | Converting data to a standard form before processing (sorted keys, trimmed whitespace, normalised URLs). | Prevents false negatives in fingerprint comparison |
| Fingerprint | A hash of an agent's identity components, used to detect changes. | Core of TBN's attestation system |
| Drift | Gradual, often undetected change in a system's behaviour or configuration from its approved state. | TBN's compliance drift score detects this |
| Circuit Breaker | An automatic shutdown mechanism triggered when operational limits are exceeded. | TBN's budget enforcement feature |
| Tamper-evident | A property where any modification to data can be detected (though not prevented). | TBN's response_hash provides this |
| Point-in-time | A snapshot of state at a specific moment, not a continuous stream. | Each TBN verification is point-in-time |
| Idempotent | An operation that produces the same result regardless of how many times it is called. | TBN's verify endpoint is read-only and idempotent |
| BICA | Bot Identity & Certification Authority — TBN's internal registry of certified agents. | The database of all certified agents |
| TRL | Technology Readiness Level (1-9 scale). TRL 7 = system prototype demonstrated in operational environment. | TBN is currently TRL 7 |
| AGPL-3.0 | Open source licence requiring anyone who modifies and deploys the code to share their modifications. | TBN's open source licence |
| EU AI Act | European Union regulation on artificial intelligence, enforceable from 2026. | Primary regulatory driver for TBN adoption |

---

## 11. Positioning & Messaging Guide

### For Developers
"pip install tbn-protocol. Three lines of code. Your agent is certified, fingerprinted, and monitored."

### For Enterprise Buyers
"One API call tells you if your agent is certified, unchanged, and within bounds. EU AI Act compliant. Continuous assurance, not periodic audits."

### For Investors
"TBN is the SSL certificate for AI agents. Network effects — every certified agent makes the registry more valuable. First integration partners already live in production."

### For Regulators
"TBN provides the technical infrastructure for EU AI Act Articles 9, 14, and 61. Automated certification, continuous monitoring, tamper-evident evidence trails."

### For Integration Partners
"We verify the agent. You handle your layer. One API call gives you the trust context you need. Clean boundary, no overlap, independently verifiable."

### Key Differentiators

1. **Runtime, not periodic** — verification happens at execution time, not quarterly
2. **Cryptographic, not trust-based** — SHA-256 hashes prove identity, not promises
3. **Open protocol** — AGPL-3.0, auditable, interoperable
4. **Network effects** — more certified agents = more valuable registry
5. **Clean boundaries** — does one thing well, integrates with everything else

---

## 12. Compliance & Regulatory Context

### EU AI Act Alignment

| Article | Requirement | TBN Feature |
|---------|-------------|-------------|
| Article 9 | Risk management system | Security certification (6 challenges) |
| Article 14 | Human oversight | Budget enforcement (automatic controls) |
| Article 61 | Post-market monitoring | Continuous monitoring + drift scoring |

### Data Handling

- TBN does not process personal data through the API
- Verification data relates to AI agents, not individuals
- API calls are logged (timestamp, key hash, endpoint, agent_id) for security and billing
- All data handling complies with UK GDPR and EU GDPR

### Audit Trail

- Every verification generates a unique `verification_id`
- Every response includes a `response_hash` for integrity verification
- All verifications are timestamped in UTC
- Partners may store verification results as long-term evidence

---

## 13. Security & Data Handling

### API Key Security

- Keys are issued per-partner after terms acceptance
- Keys must be kept confidential and never embedded in client-side code
- Compromised keys must be reported immediately for revocation and reissue
- Keys are stored as SHA-256 hashes — raw keys are shown once at issuance only

### Access Control

- All /api/verify/full calls require a valid API key
- Admin endpoints require a separate admin secret
- Partner monitoring dashboard is access-controlled
- Rate limits apply per tier

### Infrastructure

- Production server: AWS (UK region)
- HTTPS only — all traffic encrypted in transit
- Gunicorn application server behind Nginx reverse proxy
- Systemd service with automatic restart on failure

---

## 14. Quick Reference Card

```
╔══════════════════════════════════════════════════════╗
║          TBN PROTOCOL — QUICK REFERENCE              ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  WHAT WE DO:                                         ║
║  ✅ Certify agents (6 security challenges)           ║
║  ✅ Attest identity (SHA-256 fingerprint)            ║
║  ✅ Enforce budgets (auto-suspend)                   ║
║  ✅ Score drift (0-100 compliance)                   ║
║  ✅ Verify trust state (one API call)                ║
║  ✅ Provide tamper-evident evidence (response hash)  ║
║                                                      ║
║  WHAT WE DON'T DO:                                   ║
║  ❌ Judge behaviour                                  ║
║  ❌ Attribute responsibility                         ║
║  ❌ Decide admissibility                             ║
║  ❌ Reconstruct decision states                      ║
║  ❌ Enforce consequences (beyond budget)             ║
║                                                      ║
║  OUR POSITION:                                       ║
║  L1-L2 in the governance chain                       ║
║  The foundation layer everything else depends on     ║
║                                                      ║
║  LIVE NOW:                                           ║
║  • API: https://tbn.hardinai.co.uk                   ║
║  • SDK: pip install tbn-protocol                     ║
║  • Partners: CLARIXO (live), DigiEmu (integrating)   ║
║  • Licence: AGPL-3.0 + commercial                    ║
║                                                      ║
║  ENDPOINT: POST /api/verify/full                     ║
║  AUTH: Authorization: Bearer tbn_live_xxxxx           ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | May 2026 | Hardin AI Solutions | Initial release |
| 2.0 | May 2026 | Hardin AI Solutions | Added public verification registry, certification scoring (0-100), mandatory failure conditions, EU AI Act framework mapping, competitive positioning vs Raknor |

---

*This document is confidential to Hardin Enterprises Ltd staff and authorised partners. Do not distribute externally without approval.*
