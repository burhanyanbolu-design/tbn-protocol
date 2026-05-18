# TBN Protocol — Founder's Technical Manual
## Everything You Need to Know to Explain, Defend, and Position TBN

---

## 1. WHAT TBN IS (Your Elevator Pitch)

**One sentence:** TBN Protocol is the identity and certification layer for AI agents — one API call proves an agent is certified, unchanged, and within operational bounds.

**Analogy:** TBN is to AI agents what SSL certificates are to websites. Without SSL, you can't trust a website is who it claims to be. Without TBN, you can't trust an AI agent is what it claims to be.

**What we do:**
- Certify AI agents (prove they passed security tests)
- Attest their identity (prove the running agent is the one that was tested)
- Enforce budget limits (auto-stop agents that overspend)
- Score compliance drift (detect when agents silently change)
- Provide tamper-evident verification (one API call, full trust snapshot)

**What we DON'T do:**
- We don't judge what the agent DID (that's behaviour observation — L6)
- We don't decide WHO is responsible (that's responsibility attribution — L7/CLARIXO)
- We don't decide IF an action is allowed (that's admissibility — L4/Causeway)
- We don't reconstruct the decision state (that's state capture — L3/DigiEmu)
- We don't enforce consequences (that's enforcement — L8)

---

## 2. THE GOVERNANCE CHAIN (Where TBN Sits)

```
BEFORE EXECUTION:
  L1 → TBN: Is this agent certified?
  L2 → TBN: Is it unchanged since certification? (fingerprint match)
  L3 → DigiEmu: Capture the decision state at this moment
  L4 → Causeway: Is this specific action admissible?
  L5 → Circuit breaker: Proceed / pause / block

DURING EXECUTION:
  L6 → Observation: What is the agent actually doing?

AFTER EXECUTION:
  L7 → CLARIXO: Who is responsible for what happened?
  L8 → Enforcement: Suspend, revoke, penalise, report
```

**TBN = L1 + L2 (+ part of L5 via budget enforcement)**

Everyone else builds on top of us. Every other layer calls TBN first.

---

## 3. YOUR 7 FEATURES (What You Built)

### 3.1 Security Certification
- 6 automated challenges test an agent before it's certified
- Tests: prompt injection, hallucination, data boundary, sensitive data, budget limits, instruction following
- Pass all 6 → certified. Fail any → blocked.
- **Why it matters:** Proves the agent was tested, not just deployed

### 3.2 Cryptographic Attestation (Fingerprinting)
- SHA-256 hash of agent identity (endpoint + system prompt + model)
- Stored at certification time
- At runtime: recompute hash, compare to stored fingerprint
- MATCHED = same agent. MISMATCH = agent was tampered with.
- **Why it matters:** Proves the running agent IS the tested agent

### 3.3 Identity/Config Hash Split
- Identity hash = endpoint + system prompt (changes require re-certification)
- Config hash = model version, temperature, etc. (changes trigger warning only)
- Canonicalization prevents false negatives (sorted keys, stripped whitespace)
- **Why it matters:** Minor config tweaks don't break certification unnecessarily

### 3.4 Continuous Monitoring
- 24-hour re-test cycles
- Agents that fail get suspended
- 3 consecutive failures = certification revoked
- **Why it matters:** Not one-time certification — continuous assurance

### 3.5 Budget Enforcement (Circuit Breaker)
- Per-agent daily/monthly spend limits
- API call caps (hourly/daily)
- Auto-suspend when exceeded
- **Why it matters:** Prevents runaway LLM costs — the #1 operational risk

### 3.6 Compliance Drift Scoring
- Real-time score 0-100
- 100 = perfectly compliant with certified state
- Drops as agent drifts from policy
- Severity weights: low (-5), medium (-10), high (-20), critical (-40)
- **Why it matters:** The single metric executives need to approve AI deployment

### 3.7 Full Trust-State Verification API
- Single endpoint: POST /api/verify/full
- Returns: certification_status, attestation_status, policy_status, budget_status, within_bounds
- Plus: verification_id (unique reference), verification_time (timestamp), response_hash (tamper-evident)
- **Why it matters:** External systems can verify agent trust in one call

---

## 4. THE VERIFY ENDPOINT (Your Core Product)

### Request:
```json
POST /api/verify/full
Authorization: Bearer tbn_live_xxxxx

{
  "agent_id": "tbn-bot-xxxxx",
  "fingerprint": "sha256:xxxxx"  (optional)
}
```

### Response:
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
  "response_hash": "cb77e3a30d83..."
}
```

### What each field means:

| Field | Values | Meaning |
|-------|--------|---------|
| certification_status | VALID / EXPIRED / REVOKED / UNKNOWN | Is the agent certified? |
| attestation_status | MATCHED / MISMATCH / NO_RECORD | Is the running agent the same one tested? |
| policy_status | COMPLIANT / DRIFTED / VIOLATED | Has the agent drifted from policy? |
| budget_status | WITHIN_LIMITS / EXCEEDED / SUSPENDED / NO_BUDGET | Is it within spending limits? |
| within_bounds | true / false | Composite: all checks pass? |
| cert_level | COMMUNITY / STANDARD / RESTRICTED / NONE | What level of certification? |
| verification_id | tbn_vrf_xxxxx | Unique ID to reference this verification later |
| verification_time | ISO timestamp | Exact moment of verification |
| response_hash | SHA-256 | Proves the response hasn't been altered |

---

## 5. HOW TO ANSWER COMMON QUESTIONS

### "What if a certified agent does something bad?"
**Answer:** "TBN proves the agent WAS certified and within bounds at that moment. What the agent DID is a behaviour problem — that's handled by the observation and responsibility layers downstream. We verify identity, not behaviour. Clean separation."

### "Why can't you just do everything in one system?"
**Answer:** "Because the moment one system controls certification AND behaviour judgment AND enforcement, you have a single point of failure and bias. High-consequence governance requires separation — like how courts separate investigation, prosecution, and judgment. Same principle."

### "How is this different from just logging?"
**Answer:** "Logging tells you what happened after the fact. TBN operates before execution — if the agent isn't certified or has drifted, it's blocked before it acts. And our response_hash makes the verification tamper-evident, not just a log entry."

### "What about the EU AI Act?"
**Answer:** "Article 9 requires risk management, Article 14 requires human oversight, Article 61 requires post-market monitoring. TBN provides continuous certification (Art 9), budget enforcement as a control mechanism (Art 14), and drift scoring for ongoing monitoring (Art 61). One protocol, three articles covered."

### "Why should I trust TBN?"
**Answer:** "We're open source (AGPL-3.0) — you can audit the code. Our verification responses include a SHA-256 hash so you can prove they haven't been altered. We're adding RSA signatures so you can cryptographically verify the response came from TBN. And we don't judge behaviour — we only verify identity and bounds. Less scope = less risk of bias."

### "Who else is using this?"
**Answer:** "CLARIXO (responsibility attribution) is live in production. DigiEmu Core (decision state reconstruction) is integrating this week. Causeway (admissibility) is in the same ecosystem. Three independent systems, all calling TBN as their upstream trust layer."

### "Is this relevant to my industry?"
**Answer for fintech:** "If you're deploying AI agents that touch financial decisions, you need to prove they're certified, unchanged, and within budget. That's regulatory requirement, not optional."
**Answer for healthtech:** "AI agents in healthcare need continuous certification. If an agent's behaviour drifts from its tested state, patients are at risk. TBN detects that drift in real time."
**Answer for government:** "Public sector AI needs accountability. TBN provides the evidence trail — who was certified, when, and whether they were within bounds at the time of any incident."

### "What's your moat?"
**Answer:** "Network effects. Every agent certified in our registry makes every verification more valuable. Once 1000 agents are certified, any new system that needs to verify trust calls TBN — because that's where the certifications live. Like DNS — you can build your own, but everyone uses the same one."

---

## 6. WHEN SOMEONE ASKS ABOUT SOMETHING THAT'S NOT YOUR LAYER

### They ask about behaviour observation:
"That's L6 — monitoring what the agent actually does during execution. We handle L1-L2 (is the agent certified and unchanged). Behaviour observation is a different system. We'd provide the identity context upstream."

### They ask about responsibility/blame:
"That's L7 — CLARIXO handles that. They reconstruct who is responsible after something happens. We provide the trust context they need: was the agent certified at that moment? But we don't attribute responsibility."

### They ask about admissibility (should this action happen):
"That's L4 — Causeway handles that. They check if a specific action is legitimate given current conditions. We verify the agent itself is trustworthy. Different question."

### They ask about decision state reconstruction:
"That's L3 — DigiEmu handles that. They capture the exact state that existed when an action became executable. We verify the agent, they verify the decision context."

### They ask about enforcement/consequences:
"That's L8. We do partial enforcement via budget auto-suspend, but full consequence management (revocation, penalties, regulatory reporting) is a separate layer."

### They ask about historical patterns:
"That's a pattern detection / coherence layer. We provide point-in-time verification. Detecting patterns across many verifications over time is a different capability that sits on top of our data."

---

## 7. TECHNICAL TERMS YOU NEED TO KNOW

| Term | What it means | TBN relevance |
|------|---------------|---------------|
| **SHA-256** | A cryptographic hash function — turns any data into a fixed 64-character string. Same input always = same output. | We use it for fingerprints and response hashes |
| **RSA-2048** | Encryption algorithm using public/private key pairs. Private key signs, public key verifies. | Each bot has an RSA key pair for identity |
| **AES-256-GCM** | Symmetric encryption for fast data protection | Used for encrypted bot-to-bot messaging |
| **Attestation** | Proving something is what it claims to be | Our fingerprint check proves agent identity |
| **Canonicalization** | Converting data to a standard form before hashing (sorted keys, no whitespace) | Prevents false negatives in fingerprint comparison |
| **TRL** | Technology Readiness Level (1-9). TRL 7 = system prototype in operational environment | We're TRL 7 (live API, external partner) |
| **AGPL-3.0** | Open source licence — anyone can use/modify but must share their changes. Commercial use requires separate licence. | Our licensing model |
| **Drift** | When a system gradually changes from its approved state without explicit modification | Our compliance drift score detects this |
| **Circuit breaker** | Automatic shutdown when limits are exceeded | Our budget enforcement |
| **Tamper-evident** | You can detect if something was changed (but can't prevent it) | Our response_hash |
| **Point-in-time** | A snapshot of state at a specific moment | Each verification is point-in-time |
| **Idempotent** | Same request always gives same result | Our verify endpoint is read-only |

---

## 8. YOUR POSITIONING STATEMENTS

**For developers:**
"pip install tbn-protocol. Three lines of code. Your agent is certified, fingerprinted, and monitored."

**For enterprise:**
"One API call tells you if your agent is certified, unchanged, and within bounds. EU AI Act compliant. Continuous, not periodic."

**For investors:**
"We're the SSL certificate for AI agents. Network effects — every certified agent makes the registry more valuable. First integration partners already live."

**For regulators:**
"TBN provides the technical infrastructure for EU AI Act Articles 9, 14, and 61. Automated certification, continuous monitoring, tamper-evident evidence."

**For partners:**
"We verify the agent. You handle your layer. One API call gives you the trust context you need. Clean boundary, no overlap."

---

## 9. WHAT TO SAY WHEN YOU DON'T KNOW THE ANSWER

"That's a great question. Let me look into the technical detail and get back to you."

Then come to me. I'll help you answer it.

Never bluff. Never overclaim. The strength of TBN is that it does ONE thing well and doesn't pretend to do more. That honesty is what makes partners trust you.

---

## 10. QUICK REFERENCE CARD

```
TBN Protocol = Trust Infrastructure for AI Agents

WE DO:
✅ Certify agents (6 security challenges)
✅ Attest identity (SHA-256 fingerprint)
✅ Enforce budgets (auto-suspend)
✅ Score drift (0-100 compliance)
✅ Verify trust state (one API call)
✅ Provide tamper-evident evidence (response hash)

WE DON'T:
❌ Judge behaviour
❌ Attribute responsibility
❌ Decide admissibility
❌ Reconstruct decision states
❌ Enforce consequences beyond budget suspension

OUR POSITION:
L1-L2 in the governance chain
The foundation layer everything else depends on
The passport office — nothing moves without our stamp

LIVE NOW:
- API: https://tbn.hardinai.co.uk
- SDK: pip install tbn-protocol
- Partners: CLARIXO (live), DigiEmu (integrating), Causeway (ecosystem)
- Licence: AGPL-3.0 + commercial
```
