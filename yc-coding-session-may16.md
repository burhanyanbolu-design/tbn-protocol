# AI Coding Agent Session: TBN Protocol v0.1.1 → v0.1.5
## Building Complete AI Agent Governance Stack in One Session

**Project:** TBN Protocol — Trust & Governance Infrastructure for AI Agents
**Date:** May 16, 2026
**Duration:** ~10 hours (single session)
**Tool:** Kiro (AWS AI IDE with Claude)
**Outcome:** Shipped 5 versions to PyPI + GitHub, built 7 new features, deployed to production

---

## What We Built

### Starting Point
- Basic demo page with 3-step certification flow
- No budget enforcement, no monitoring, no compliance tracking
- Admin page with no password protection

### End Result (v0.1.5)
- Full 14-step governance demo (simulated, public)
- Full 14-step admin portal (real API calls, password-protected)
- 7 new backend systems deployed to production
- SDK with one-line integration
- Early access waitlist page
- All published to PyPI and GitHub

---

## Features Built This Session

### 1. Proof of Attestation (The Moat)
SHA-256 fingerprint of bot identity stored at certification time. Platforms call /verify to check running bot matches certified state. If bot changes → access denied.

```python
# API: POST /api/security-challenge/verify
# Returns: verified: true/false, identity_match, config_match
```

### 2. Identity/Config Hash Split + Canonicalization
Separated "who the bot is" (identity hash) from "how it behaves" (config hash). Identity changes require re-certification. Config changes only trigger warnings. Added canonicalization (sorted keys, stripped whitespace) to prevent false negatives.

### 3. Continuous Monitoring
24-hour re-test cycles. Bots that fail get suspended. Health dashboard tracks status (healthy/expired/failed). 3 consecutive failures = certification revoked.

```python
# API: GET /api/security-challenge/monitor/status
# API: POST /api/security-challenge/monitor/retest
# API: GET /api/security-challenge/monitor/overdue
```

### 4. Budget/Cost Enforcement (Circuit Breaker)
Per-bot daily/monthly spend limits. API call caps (hourly/daily). Real-time tracking. Automatic suspension when limits exceeded.

```python
# API: POST /api/budget/set
# API: POST /api/budget/track → returns {allowed: true/false}
# API: GET /api/budget/check/<bot_id>
# API: GET /api/budget/dashboard
```

### 5. Webhook Notifications
Slack/custom URL alerts when bots fail re-tests, hit budget limits, or drift from policy. Async delivery with delivery logging.

```python
# API: POST /api/webhooks/register
# API: POST /api/webhooks/test
# API: GET /api/webhooks/deliveries
```

### 6. Compliance Drift System
Set policies per bot. Check current state against policy. Returns compliance score (0-100) and lists all violations. The "single pane of glass" for executives.

```python
# API: POST /api/compliance/policy/set
# API: POST /api/compliance/check → returns {score, drifts}
# API: GET /api/compliance/dashboard
```

### 7. SDK Simplification
One-line integration that registers, fingerprints, and certifies a bot:

```python
from tbn import TBNClient
client = TBNClient("MyBot", "SEARCH")
client.attach(endpoint="https://mybot.com/api", system_prompt="You are a search bot")
# Done — registered, fingerprinted, certified.
```

---

## Testing & Verification

All features tested on live production server with automated test scripts:

```
=== TBN Feature Tests ===
1. Register Bot... ✅ tbn-bot-54fd152c4762c0cc
2. Start Certification (Proof of Attestation)... ✅ Fingerprint: 4fc8bf3d...
3. Running 6 challenges... ✅ All 6 passed
4. Evaluate... ✅ PASS | Rate: 100.0% | Level: RESTRICTED
5. Verify Attestation (same config)... ✅ VERIFIED — fingerprint matches
6. Verify with changed config... ✅ IDENTITY_MISMATCH (correctly rejects)
7. Monitoring Status... ✅ 1 healthy bot tracked
8. Set Budget... ✅ £10/day, 500 calls/day
9. Track Usage... ✅ Allowed, within budget
10. Check Budget... ✅ 0.5% used
=== ALL TESTS COMPLETE ===
```

---

## Deployment Flow

Each feature followed this cycle:
1. Write code locally
2. Deploy via SCP to AWS Lightsail
3. Restart systemd service
4. Test on live server
5. Commit to GitHub
6. Bump version, build, publish to PyPI

```bash
# Typical deployment (repeated ~20 times this session)
scp -i .ssh_temp_key api/security_challenge.py ubuntu@3.11.229.68:/opt/tbn-protocol/api/
ssh ubuntu@3.11.229.68 "sudo systemctl restart tbn"
git add . && git commit -m "v0.1.x: feature" && git push origin main
python -m build && twine upload dist/*
```

---

## Versions Shipped

| Version | Features | Time |
|---------|----------|------|
| 0.1.1 | 14-step demo + admin portal + password protection | Hour 2 |
| 0.1.2 | Proof of Attestation + Monitoring + Budget Enforcement | Hour 4 |
| 0.1.3 | Identity/Config hash split + canonicalization | Hour 5 |
| 0.1.4 | SDK simplified (attach, budget, health, verify methods) | Hour 6 |
| 0.1.5 | Webhooks + Compliance Drift system | Hour 7 |

---

## Key Problem-Solving Moments

### Bug: Step 12 "Verify Attestation" always showing MISMATCH
- **Root cause found:** Sub-agent wrote wrong API field names (`challenge_type` instead of `challenge`, `response` instead of `bot_response`). Challenges were never being recorded, so evaluation had nothing to evaluate, so no PASS attestation existed.
- **Fix:** Corrected field names in the submit call. Cleared stale data. Verified with automated test script.
- **Lesson:** Always test the full chain, not just individual endpoints.

### Architecture Decision: Identity vs Config Hash Split
- **Context:** YC office hours feedback said "minor config changes shouldn't break certification"
- **Solution:** Split fingerprint into identity_hash (endpoint + system prompt) and config_hash (model, temperature, etc). Identity change = must re-certify. Config change = warning only.
- **Implementation:** Canonicalization layer (sorted keys, stripped whitespace, normalized endpoints) prevents false negatives from formatting differences.

---

## Session Workflow

The session demonstrated:
- **Rapid iteration:** 5 versions shipped in ~8 hours
- **Real-time feedback loop:** Built feature → deployed → tested → got YC office hours feedback → built next feature
- **Production-first:** Every feature deployed to live server immediately, not just local
- **Full-stack:** Backend (Python/Flask), frontend (HTML/JS), deployment (AWS/SSH), package management (PyPI), version control (Git)

---

## Tools Used
- **Kiro** (AWS AI IDE with Claude) — all code generation, architecture decisions, deployment
- **AWS Lightsail** — production hosting
- **PyPI** — package distribution
- **GitHub** — version control
- **Google Analytics** — traffic monitoring

---

## Links
- Live demo: https://tbn.hardinai.co.uk/demo
- Admin portal: https://tbn.hardinai.co.uk/certification/portal
- PyPI: https://pypi.org/project/tbn-protocol/0.1.5/
- GitHub: https://github.com/burhanyanbolu-design/tbn-protocol
- Early access: https://tbn.hardinai.co.uk/early-access
