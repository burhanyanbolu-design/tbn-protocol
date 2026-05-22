# The Trust Identity Layer

## Defining Governance at the Agent Boundary

---

**TBN Protocol™**
**Category Definition Document**

**Version 1.0**
**May 2026**

**Hardin Enterprises Ltd**
London, United Kingdom

---

**Author:** Burhan Yanbolu
**Contact:** burhan@hardinai.co.uk
**Protocol:** https://tbn.hardinai.co.uk
**Source:** https://github.com/burhanyanbolu-design/tbn-protocol
**License:** AGPL-3.0 with commercial licensing

---

## Table of Contents

1. Executive Summary
2. The Structural Shift in AI Governance
3. The Agent Boundary Problem
4. Why Existing Categories Are Insufficient
5. Defining the Category: Trust Identity Infrastructure
6. TBN Protocol — Core Architecture
7. The Trust Verification Model
8. Certification Levels
9. The Governance Ledger
10. Cryptographic Attestation
11. Interoperability Design
12. Enterprise Integration Patterns
13. Regulatory Alignment
14. Comparison with Adjacent Categories
15. Implementation Status
16. Future Direction
17. Conclusion

---

## 1. Executive Summary

As artificial intelligence transitions from single-model deployments into autonomous multi-agent architectures, a foundational governance gap has emerged that no existing category adequately addresses.

The gap is not in model evaluation. It is not in observability. It is not in policy management.

The gap is in **trust identity** — the ability to determine, in real-time, whether an AI agent is who it claims to be, whether it remains authorised to act, and who bears accountability for its actions.

This document defines a new infrastructure category — **Trust Identity Infrastructure for AI Agents** — and presents TBN Protocol as the first implementation of this category.

TBN Protocol operates at the agent boundary: the layer between an agent's existence and its right to participate. It resolves trust deterministically before interaction occurs, not after consequence materialises.

The core thesis is simple:

**Before you can govern what an agent does, you must first govern whether it should be acting at all.**

---

## 2. The Structural Shift in AI Governance

### 2.1 The Historical Model

For the past decade, AI governance has been structured around a set of well-understood concerns:

- **Model evaluation** — Is the model accurate? Is it biased? Does it perform within acceptable parameters?
- **Explainability** — Can we understand why the model produced a given output?
- **Audit** — Can we reconstruct what happened after the fact?
- **Human oversight** — Is there a human in the loop for critical decisions?
- **Policy compliance** — Does the system operate within regulatory boundaries?
- **Observability** — Can we monitor the system's behaviour in production?

These concerns remain valid. They are necessary components of responsible AI deployment.

They are not sufficient for what comes next.

### 2.2 The Multi-Agent Transition

The AI industry is undergoing a structural transition from single-model systems to multi-agent architectures. This transition introduces fundamentally new governance challenges:

**Agents act autonomously.** They do not wait for human approval on every action. They make decisions at machine speed, often in contexts where human review is impractical or impossible.

**Agents interact with other agents.** In multi-agent systems, the counterparty is not a human user — it is another autonomous system. Trust between agents cannot be established through human intuition.

**Agents cross organisational boundaries.** An agent deployed by Company A may interact with an agent deployed by Company B. Neither organisation has visibility into the other's internal governance.

**Agents accumulate authority.** Through delegation chains, an agent may acquire the ability to act in ways that exceed its original mandate. Without continuous trust verification, scope creep is invisible.

**Agents operate in regulated environments.** Healthcare, finance, legal, infrastructure — domains where accountability is not optional and "we didn't know" is not an acceptable answer.

### 2.3 The New Question

This transition introduces a governance question that existing frameworks do not address:

**Was this agent legitimately trusted at the exact moment it acted?**

Not "was it trusted when it was deployed." Not "was it trusted when it was last audited." Not "was it trusted according to its configuration file."

Was it trusted *right now*, at the moment of interaction?

This is the question TBN Protocol answers.

---

## 3. The Agent Boundary Problem

### 3.1 Definition

The **agent boundary** is the logical layer between an AI agent's existence and its right to participate in a system.

An agent may exist — it may be deployed, running, and technically functional — without being legitimately authorised to act. The agent boundary is where this distinction is resolved.

### 3.2 The Degradation Problem

Trust is not static. It degrades over time and in response to events:

- A certification may expire
- An accountable party may leave the organisation
- A compliance requirement may change
- A security incident may compromise the agent's integrity
- Behavioural drift may move the agent outside its declared scope
- A regulatory action may invalidate the agent's operating authority

In all of these cases, the agent continues to function technically. It responds to requests. It produces outputs. It appears healthy.

But its trust state has degraded. It is no longer legitimately authorised to act.

### 3.3 The Invisibility Problem

Trust degradation is invisible at the execution layer. A platform interacting with an agent sees:

- A valid API response
- Correct authentication credentials
- Normal latency and throughput
- No error codes

Nothing in the execution layer signals that the agent's trust has degraded. The degradation exists only at the trust-identity boundary — a layer that, until now, has not existed as infrastructure.

### 3.4 The Accountability Gap

When an agent acts without valid trust, accountability becomes ambiguous:

- Who authorised this action?
- Was the certification still valid?
- Did the agent exceed its declared scope?
- Can we prove, cryptographically, what the trust state was at the moment of action?

Without trust identity infrastructure, these questions are answered retrospectively — through logs, interviews, and forensic reconstruction. This is governance after consequence. It is not governance.

---

## 4. Why Existing Categories Are Insufficient

### 4.1 AI Observability

**What it does:** Monitors model performance, latency, throughput, and drift in production.

**Why it's insufficient:** Observability tells you what happened. It does not tell you whether the agent was trusted when it happened. An agent can produce perfect metrics while operating with revoked certification.

### 4.2 AI Safety

**What it does:** Constrains model behaviour through guardrails, content filters, and alignment techniques.

**Why it's insufficient:** AI safety operates at the model output layer. It does not address agent-level identity, accountability, or organisational trust. A safe model inside an untrusted agent is still a governance failure.

### 4.3 API Security / Authentication

**What it does:** Verifies that API calls come from authenticated sources using keys, tokens, or certificates.

**Why it's insufficient:** Authentication proves identity at the network layer. It does not prove certification, scope compliance, or ongoing trust. An API key does not expire when an agent's behaviour drifts outside its declared boundary.

### 4.4 AI Governance Platforms

**What they do:** Manage policies, workflows, approvals, and compliance documentation.

**Why they're insufficient:** Governance platforms manage process. They do not resolve trust in real-time at the point of interaction. A policy document does not prevent an untrusted agent from acting.

### 4.5 Identity & Access Management (IAM)

**What it does:** Manages human user identity, roles, and permissions.

**Why it's insufficient:** IAM was designed for human users. AI agents require different primitives: certification levels, operational boundaries, behavioural monitoring, instant revocation, and cryptographic attestation. Bolting agent identity onto human IAM creates a category error.

### 4.6 The Gap

None of these categories answer the foundational question:

*Is this agent currently trusted, certified, accountable, and operating within its declared scope — and can I verify that cryptographically, right now, before I interact with it?*

This is the gap that Trust Identity Infrastructure fills.

---

## 5. Defining the Category: Trust Identity Infrastructure

### 5.1 Category Definition

**Trust Identity Infrastructure** is the foundational layer that resolves whether an AI agent is legitimately trusted at the moment of interaction.

It operates upstream of execution, upstream of decision-making, and upstream of runtime admissibility. It answers the prerequisite question that all other governance layers depend on:

*Should this agent be participating at all?*

### 5.2 Category Characteristics

Trust Identity Infrastructure must provide:

1. **Cryptographic agent identity** — Every agent has a verifiable, unforgeable identity tied to a named accountable party.

2. **Real-time trust resolution** — Trust state is resolved at the moment of query, not cached or assumed.

3. **Deterministic outcomes** — Every verification produces an unambiguous result. No probabilistic trust scores.

4. **Instant revocation** — Trust can be removed immediately, with propagation across all integrated systems.

5. **Operational boundary enforcement** — Agents declare what they are authorised to do. Verification checks scope, not just identity.

6. **Cryptographic attestation** — Every trust decision is signed and independently verifiable by any party.

7. **Organisational accountability** — Every agent has a named human or organisation that bears responsibility.

8. **Cross-platform interoperability** — Trust verification works across organisational and platform boundaries.

### 5.3 Category Position

Trust Identity Infrastructure sits at the base of the AI governance stack:

```
┌─────────────────────────────────────────────┐
│         Application / Platform Layer         │
├─────────────────────────────────────────────┤
│         Runtime Admissibility Layer          │
│    (e.g., FlowSignal — ALLOW/ESCALATE/      │
│     REFUSE at execution commitment)         │
├─────────────────────────────────────────────┤
│       Decision-State Verification Layer      │
│    (e.g., DigiEmu — deterministic state     │
│     hashing at the decision boundary)       │
├─────────────────────────────────────────────┤
│        Trust Identity Layer (TBN)            │
│    Agent identity, certification, scope,    │
│    revocation — PASS / WARN / FAIL          │
├─────────────────────────────────────────────┤
│         Cryptographic Foundation             │
│    RSA-PSS-SHA256 signing, hash chains,     │
│    public key infrastructure                │
└─────────────────────────────────────────────┘
```

Every layer above depends on the trust identity layer. You cannot determine runtime admissibility without first knowing whether the agent is trusted. You cannot verify decision-state without first knowing whether the agent is certified to make decisions.

Trust identity is foundational. It is not optional.

---

## 6. TBN Protocol — Core Architecture

### 6.1 Overview

TBN Protocol (Trusted Bot Network Protocol) is the first implementation of Trust Identity Infrastructure. It provides a complete verification layer that any platform can integrate to resolve agent trust in real-time.

### 6.2 Core Primitives

| Primitive | Function | Endpoint |
|-----------|----------|----------|
| **Register** | Cryptographic registration of an AI agent with accountable party | `POST /api/register` |
| **Certify** | Issue certification at a defined level (L1–L5) | `POST /api/certify` |
| **Verify** | Real-time trust resolution with signed attestation | `POST /api/verify/full` |
| **Revoke** | Instant trust removal, propagated across all integrations | `POST /api/revoke` |
| **Governance** | Rule-based pre-execution checks (rate limits, scope, time) | `POST /api/governance/rules/check` |
| **Ledger** | Hash-chained audit trail of all trust events | `GET /api/governance/ledger/{company}` |

### 6.3 Design Principles

**Deterministic.** Every verification produces exactly one of three outcomes: PASS, WARN, or FAIL. There are no probability scores, no confidence intervals, no "maybe." Trust is binary with a warning state.

**Stateless verification.** Any party can verify an agent's trust state at any time without prior context. The verification response contains everything needed to make a trust decision.

**Cryptographically signed.** Every verification response is signed with TBN's private key using RSA-PSS with SHA-256. Any party can independently verify the signature using TBN's published public key.

**Zero-trust by default.** An unregistered agent receives FAIL. An uncertified agent receives WARN. Only a registered, certified, in-scope agent receives PASS. Trust is earned, not assumed.

**Instant revocation.** When trust is revoked, the next verification request returns FAIL. There is no propagation delay, no cache invalidation window, no grace period.

---

## 7. The Trust Verification Model

### 7.1 Verification Flow

```
Requesting Platform          TBN Protocol              Agent Registry
       │                          │                          │
       │  POST /api/verify/full   │                          │
       │  { agent_id, action }    │                          │
       │─────────────────────────>│                          │
       │                          │  Lookup agent identity   │
       │                          │─────────────────────────>│
       │                          │                          │
       │                          │  Check certification     │
       │                          │  Check scope boundary    │
       │                          │  Check revocation state  │
       │                          │  Check governance rules  │
       │                          │<─────────────────────────│
       │                          │                          │
       │                          │  Sign response (RSA-PSS) │
       │                          │                          │
       │  { status: PASS/WARN/    │                          │
       │    FAIL, trust_state,    │                          │
       │    signature }           │                          │
       │<─────────────────────────│                          │
       │                          │                          │
```

### 7.2 Verification Outcomes

**PASS** — The agent is:
- Registered with a valid identity
- Certified at an appropriate level
- Operating within its declared scope
- Not revoked
- Compliant with all active governance rules

The requesting platform can proceed with confidence.

**WARN** — The agent is:
- Registered but not yet certified, OR
- Certified but operating in an ambiguous scope area, OR
- Subject to a governance rule that requires escalation

The requesting platform should proceed with caution or escalate to human review.

**FAIL** — The agent is:
- Not registered (unknown identity), OR
- Certification has been revoked, OR
- Operating outside its declared scope, OR
- Blocked by an active governance rule

The requesting platform should refuse interaction.

### 7.3 Verification Response Structure

```json
{
  "verification_id": "vrf_8b3f1e7a_2026-05-21T14:30:00Z",
  "agent_id": "agent.demo.001",
  "status": "PASS",
  "trust_state": {
    "identity_verified": true,
    "certification_level": "L3",
    "certification_valid": true,
    "scope_compliant": true,
    "revoked": false,
    "accountable_party": "DigiEmu Ltd"
  },
  "governance": {
    "rules_checked": 4,
    "rules_triggered": 0,
    "action_allowed": true
  },
  "verified_at": "2026-05-21T14:30:00Z",
  "expires_at": "2026-05-21T14:35:00Z",
  "signature": "RSA-PSS-SHA256:base64...",
  "public_key_url": "https://tbn.hardinai.co.uk/api/signing/public-key"
}
```

---

## 8. Certification Levels

TBN Protocol defines five certification levels, each representing increasing trust assurance:

### Level 1 — Registered

- Agent identity is recorded
- Accountable party is named
- No verification of capabilities or behaviour
- Minimum viable trust

### Level 2 — Verified

- Identity confirmed through external validation
- Operational boundary declared and reviewed
- Basic behavioural baseline established
- Suitable for low-risk, non-critical interactions

### Level 3 — Certified

- Full capability assessment completed
- Operational boundary tested and confirmed
- Governance rules active and enforced
- Behavioural monitoring in place
- Suitable for standard enterprise operations

### Level 4 — Audited

- Independent third-party audit completed
- Compliance with relevant regulatory frameworks confirmed
- Continuous monitoring with anomaly detection
- Incident response procedures documented and tested
- Suitable for regulated environments

### Level 5 — Sovereign

- Highest assurance level
- Continuous real-time verification
- Cross-jurisdictional compliance confirmed
- Full governance ledger with hash-chain integrity
- Suitable for critical infrastructure and high-stakes autonomous operations

### Certification Decay

Certification is not permanent. It decays under defined conditions:

- Time-based expiry (configurable per level)
- Behavioural anomaly detection
- Governance rule violations
- Accountable party changes
- Scope boundary modifications

When certification decays, the agent's verification status transitions from PASS to WARN until recertification is completed.

---

## 9. The Governance Ledger

### 9.1 Purpose

The governance ledger provides an immutable, hash-chained record of all trust events in the system. It serves as the authoritative audit trail for:

- Agent registrations
- Certification grants and revocations
- Verification requests and outcomes
- Governance rule triggers
- Behavioural anomalies
- Scope boundary changes

### 9.2 Hash Chain Integrity

Each ledger entry contains a SHA-256 hash of the previous entry, creating a tamper-evident chain:

```json
{
  "entry_id": 1047,
  "timestamp": "2026-05-21T14:30:00Z",
  "event_type": "CERTIFICATION_GRANTED",
  "agent_id": "agent.demo.001",
  "details": {
    "level": "L3",
    "granted_by": "tbn_authority",
    "valid_until": "2026-11-21T14:30:00Z"
  },
  "previous_hash": "sha256:a4f2e8...",
  "entry_hash": "sha256:7b3c1d..."
}
```

### 9.3 Verification

Any party can verify ledger integrity by:

1. Requesting the ledger for a given agent or company
2. Recomputing the hash chain from the first entry
3. Confirming that each entry's hash matches the next entry's `previous_hash`

If any entry has been tampered with, the chain breaks and the tampering is detectable.

---

## 10. Cryptographic Attestation

### 10.1 Signing Method

TBN Protocol uses **RSA-PSS with SHA-256** for all cryptographic attestations. This provides:

- **Non-repudiation** — TBN cannot deny having issued a verification
- **Independent verification** — Any party can verify using the published public key
- **Tamper evidence** — Any modification to the signed payload invalidates the signature

### 10.2 Public Key Distribution

TBN's public key is available at:

```
GET https://tbn.hardinai.co.uk/api/signing/public-key
```

This endpoint returns the RSA public key in PEM format, along with metadata about the signing algorithm and key size.

### 10.3 Verification by Third Parties

Any platform, auditor, or counterparty can independently verify a TBN attestation:

1. Extract the `signature` field from the verification response
2. Fetch TBN's public key from the published endpoint
3. Verify the RSA-PSS-SHA256 signature against the response payload
4. If valid, the verification was genuinely issued by TBN

This enables **trustless verification** — you do not need to trust the party presenting the verification. You only need to trust TBN's public key.

---

## 11. Interoperability Design

### 11.1 Philosophy

TBN Protocol is designed to be **complementary, not competing**. It provides the trust identity foundation that other governance systems build upon.

### 11.2 Confirmed Interoperability

**DigiEmu (Decision-State Verification)**

- First interoperability proof confirmed May 2026
- DigiEmu verifies decision-state at the hash boundary
- TBN verifies agent trust at the identity boundary
- Shared boundary: `agent_id` + `moment_id` + `snapshot_hash`
- Both systems compute identical SHA-256 hashes of canonical decision snapshots
- Systems remain fully independent while sharing a verifiable trust boundary

### 11.3 Designed Interoperability

**Runtime Admissibility Systems (e.g., FlowSignal)**

TBN's PASS/WARN/FAIL maps naturally to runtime admissibility:

| TBN Output | Admissibility Input |
|------------|-------------------|
| PASS | Agent trusted — proceed to admissibility check |
| WARN | Agent ambiguous — escalate before admissibility |
| FAIL | Agent untrusted — refuse without admissibility check |

Runtime admissibility operates downstream of trust identity. If the agent is not trusted, the admissibility question is moot.

**Enterprise IAM Systems**

TBN extends organisational IAM to AI agents:

- Human users authenticate through existing IAM
- AI agents authenticate through TBN
- Both produce verifiable identity attestations
- Unified audit trail across human and agent actions

**Compliance Platforms**

TBN provides trust attestations that compliance platforms can consume:

- Real-time certification status for compliance dashboards
- Governance ledger entries for audit reports
- Signed verification records for regulatory evidence

### 11.4 Integration Protocol

Any platform can integrate TBN verification with a single API call:

```
POST https://tbn.hardinai.co.uk/api/verify/full
Content-Type: application/json

{
  "bot_id": "agent.demo.001",
  "action": "execute_trade",
  "context": {
    "platform": "trading-system",
    "environment": "production"
  }
}
```

Response time: <100ms for standard verification.

---

## 12. Enterprise Integration Patterns

### 12.1 Gateway Pattern

The most common integration pattern places TBN verification at the API gateway:

```
Client Request → API Gateway → TBN Verify → [PASS] → Agent Execution
                                           → [FAIL] → Reject (403)
                                           → [WARN] → Escalate / Queue
```

Every request to an AI agent passes through trust verification before reaching the agent. This ensures no untrusted agent can act, regardless of the application logic.

### 12.2 Sidecar Pattern

For microservice architectures, TBN verification runs as a sidecar:

- Each agent service has a TBN verification sidecar
- The sidecar intercepts outbound requests
- Verification occurs before the request leaves the service boundary
- No changes to application code required

### 12.3 Event-Driven Pattern

For event-driven architectures:

- Events are published to a message queue
- A TBN verification consumer checks agent trust before event processing
- Untrusted events are routed to a dead-letter queue
- Trusted events proceed to processing

### 12.4 Batch Verification

For high-throughput systems, TBN supports batch verification:

```
POST /api/verify/batch
{
  "verifications": [
    { "bot_id": "agent.001", "action": "read" },
    { "bot_id": "agent.002", "action": "write" },
    { "bot_id": "agent.003", "action": "execute" }
  ]
}
```

Returns individual PASS/WARN/FAIL for each agent in a single request.

---

## 13. Regulatory Alignment

### 13.1 EU AI Act

TBN Protocol aligns with the EU AI Act's requirements for:

- **Transparency** — Agent identity and accountability are publicly verifiable
- **Human oversight** — Governance rules can enforce human-in-the-loop for high-risk actions
- **Risk management** — Certification levels map to risk categories
- **Record-keeping** — The governance ledger provides the required audit trail
- **Accountability** — Every agent has a named responsible party

### 13.2 UK AI Safety Framework

TBN supports the UK framework's principles of:

- **Safety** — Untrusted agents are blocked from acting
- **Transparency** — All trust decisions are signed and auditable
- **Fairness** — Governance rules are applied consistently
- **Accountability** — Clear chain of responsibility from agent to human
- **Contestability** — Verification decisions can be challenged and reviewed

### 13.3 NIST AI Risk Management Framework

TBN maps to NIST AI RMF functions:

| NIST Function | TBN Implementation |
|---------------|-------------------|
| GOVERN | Governance rules, certification levels, accountability |
| MAP | Operational boundary declaration, scope definition |
| MEASURE | Behavioural monitoring, anomaly detection, compliance drift |
| MANAGE | Revocation, rule enforcement, escalation |

### 13.4 Financial Services (FCA/PRA)

For UK financial services, TBN provides:

- Audit trail meeting FCA record-keeping requirements
- Real-time monitoring for PRA operational resilience
- Clear accountability chains for Senior Managers Regime
- Instant revocation for incident response

---

## 14. Comparison with Adjacent Categories

| Category | Primary Question | Timing | TBN Difference |
|----------|-----------------|--------|----------------|
| AI Observability | What is the model doing? | During/after execution | Trust state before execution |
| AI Safety | Is the output harmful? | At output generation | Is the agent authorised to generate? |
| API Security | Is this request authenticated? | At network boundary | Is this agent certified and in-scope? |
| AI Governance Platforms | Are policies defined? | At policy creation | Are policies enforced in real-time? |
| IAM | Is this user who they claim? | At login | Is this agent still trusted right now? |
| Runtime Admissibility | Is this action still legitimate? | At execution commitment | Is this agent still trusted to attempt? |
| **Trust Identity (TBN)** | **Should this agent be acting?** | **Before any interaction** | **Foundational — all others depend on this** |

---

## 15. Implementation Status

### 15.1 Current State (May 2026)

| Component | Status |
|-----------|--------|
| Core verification API | ✅ Live in production |
| Cryptographic signing (RSA-PSS-SHA256) | ✅ Live |
| Certification levels (L1–L5) | ✅ Implemented |
| Governance engine (rules, ledger, behaviour) | ✅ Live |
| DigiEmu interoperability | ✅ First proof confirmed |
| Partner registration | ✅ Live |
| Public key distribution | ✅ Published |
| Batch verification | ✅ Implemented |
| Budget enforcement | ✅ Live |
| Compliance drift detection | ✅ Live |
| PyPI package | ✅ Published (v0.1.0) |
| Open source (AGPL-3.0) | ✅ Available |

### 15.2 Production Endpoints

| Endpoint | URL |
|----------|-----|
| Dashboard | https://tbn.hardinai.co.uk |
| Verification API | https://tbn.hardinai.co.uk/api/verify/full |
| Public Key | https://tbn.hardinai.co.uk/api/signing/public-key |
| DigiEmu Interop | https://tbn.hardinai.co.uk/api/digiemu/status |
| Governance | https://tbn.hardinai.co.uk/api/governance/ |
| Partner Registration | https://tbn.hardinai.co.uk/partners |

### 15.3 Integration Partners

| Partner | Integration Type | Status |
|---------|-----------------|--------|
| DigiEmu | Decision-state verification | ✅ Interop proof confirmed |
| Boomi | Enterprise workflow integration | ✅ Connector live |

---

## 16. Future Direction

### 16.1 Near-Term (Q3 2026)

- Full live boundary test with DigiEmu (end-to-end signature verification)
- Additional partner integrations
- SDK releases (Python, JavaScript, Go)
- Certification decay automation
- Enhanced behavioural anomaly detection

### 16.2 Medium-Term (Q4 2026 – Q1 2027)

- Federated trust networks (multiple TBN nodes)
- Cross-jurisdictional compliance mapping
- Hardware security module (HSM) integration for key management
- Real-time certification streaming (WebSocket)
- Enterprise SSO integration for accountable party verification

### 16.3 Long-Term Vision

TBN Protocol becomes the standard trust identity layer for AI agents — the equivalent of what SSL/TLS became for web traffic, but for agent trust.

Every AI agent that acts autonomously should be:
- Registered
- Certified
- Verifiable
- Revocable
- Accountable

This is not a feature. It is infrastructure.

---

## 17. Conclusion

The model is rarely the most expensive part of AI risk. The operating gap is.

But the operating gap begins at a more fundamental level than most governance frameworks acknowledge. Before you can govern execution, you must govern trust. Before you can govern trust, you must govern identity. Before you can govern identity, you must have infrastructure that makes identity verifiable, certification enforceable, and revocation instant.

That infrastructure does not exist in the current AI governance stack. It is not provided by observability platforms, safety tools, API gateways, or policy management systems.

It is a new category: **Trust Identity Infrastructure**.

TBN Protocol is the first implementation of this category. It operates at the agent boundary — the layer between existence and participation — and resolves trust deterministically before interaction occurs.

Three outcomes. No ambiguity. Cryptographically signed.

**PASS. WARN. FAIL.**

Not audit after breach. Not policy after incident. Not accountability after harm.

**Governance before interaction. Trust before execution. Identity before autonomy.**

This is the foundation. Everything else builds on top of it.

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| Agent Boundary | The logical layer between an AI agent's existence and its right to participate |
| Trust Identity | The verifiable combination of identity, certification, scope, and accountability |
| Certification Level | A defined tier (L1–L5) representing the assurance level of an agent's trust |
| Operational Boundary | The declared scope of actions an agent is authorised to perform |
| Governance Ledger | An immutable, hash-chained record of all trust events |
| Trust Degradation | The process by which an agent's trust state weakens over time or due to events |
| Cryptographic Attestation | A digitally signed statement that can be independently verified |
| Deterministic Outcome | A verification result that is unambiguous and reproducible |

## Appendix B: API Reference Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /api/register | Register a new AI agent |
| POST | /api/certify | Issue or update certification |
| POST | /api/verify/full | Full trust verification with signature |
| POST | /api/verify/batch | Batch verification for multiple agents |
| POST | /api/revoke | Revoke agent certification |
| GET | /api/signing/public-key | Retrieve TBN public key |
| POST | /api/governance/rules/check | Check governance rules |
| GET | /api/governance/ledger/{company} | Retrieve governance ledger |
| POST | /api/digiemu/verify | DigiEmu boundary verification |
| GET | /api/digiemu/status | Interop layer health |

---

*© 2026 Hardin Enterprises Ltd. All rights reserved.*
*TBN Protocol™ is a trademark of Hardin Enterprises Ltd.*
*Licensed under AGPL-3.0. Commercial licensing available.*
*Contact: burhan@hardinai.co.uk*
