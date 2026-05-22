# TBN-DigiEmu Interoperability Protocol

**Version:** 1.0.0  
**Date:** 21 May 2026  
**Status:** First boundary test ready  
**Authors:** Burhan Yanbolu (TBN), Bruno (DigiEmu)

---

## Overview

This document defines the interoperability boundary between **TBN Protocol** (agent trust verification) and **DigiEmu** (decision-state reconstruction and verification).

The two systems remain fully independent. They do not merge, absorb, or depend on each other's internals. They meet at a shared boundary defined by three values:

- `agent_id` — identifies the agent
- `moment_id` — identifies the point in time
- `snapshot_hash` — cryptographic proof of the decision state

---

## Boundary Definition

### TBN Side (Agent Trust Verification)

TBN is responsible for:
- Agent identity verification
- Trust status (valid, revoked, uncertified)
- Certification level
- Signed attestation of verification result

TBN does **not** reconstruct the decision state. TBN does **not** verify policy compliance or execution correctness.

### DigiEmu Side (Decision-State Verification)

DigiEmu is responsible for:
- Decision context reconstruction
- Policy state verification
- Input state tracking
- Execution state recording
- Output state verification
- Canonical snapshot hash computation

DigiEmu does **not** verify agent identity. DigiEmu does **not** issue trust attestations.

### Shared Boundary

| Field | Source | Purpose |
|-------|--------|---------|
| `agent_id` | Both | Identifies the agent being verified |
| `moment_id` | Both | Identifies the exact moment/decision |
| `snapshot_hash` | DigiEmu computes, TBN references | Cryptographic proof of decision state |
| `status` | Both | PASS / FAIL semantics |

---

## Data Structures

### DigiEmu Canonical Snapshot

```json
{
  "schema_version": "digiemu.snapshot.v1",
  "agent_id": "agent.demo.001",
  "moment_id": "moment.2026-05-21T12-00-00Z",
  "decision_context": {
    "intent": "summarize_text",
    "input_ref": "input.demo.001",
    "policy_ref": "policy.allow_summary.v1"
  },
  "policy_state": {
    "policy_id": "policy.allow_summary.v1",
    "rules": {
      "intent_must_equal": "summarize_text",
      "input_text_required": true
    }
  },
  "input_state": {
    "input_id": "input.demo.001",
    "text": "This is a minimal test input for the TBN and DigiEmu boundary validation."
  },
  "execution_state": {
    "actor": "agent.demo.001",
    "action_type": "summary_generation",
    "status": "completed"
  },
  "output_state": {
    "output_id": "output.demo.001",
    "summary": "Minimal test input for validating the TBN and DigiEmu boundary."
  }
}
```

### TBN Verification Result

```json
{
  "schema_version": "tbn.verification_result.v1",
  "agent_id": "agent.demo.001",
  "moment_id": "moment.2026-05-21T12-00-00Z",
  "trust_state": {
    "agent_verified": true,
    "identity_status": "verified",
    "trust_status": "valid",
    "cert_level": "STANDARD"
  },
  "verification_result": {
    "status": "PASS",
    "verified_at": "2026-05-21T12:00:05Z",
    "method": "tbn_agent_trust_verification"
  },
  "external_references": {
    "digiemu_snapshot_hash": "sha256:<computed_hash>",
    "digiemu_schema_version": "digiemu.snapshot.v1"
  },
  "tbn_signature": "<RSA-PSS-SHA256-base64>"
}
```

---

## Hash Computation Method

Both systems must compute the hash identically:

1. Serialize the snapshot as JSON with **sorted keys**
2. Use minimal separators: `(",", ":")`  — no insignificant whitespace
3. Encode as **UTF-8**
4. Compute **SHA-256** hash
5. Prefix with `sha256:`

```python
import json, hashlib

canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
hash_hex = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
snapshot_hash = f"sha256:{hash_hex}"
```

---

## API Endpoints (TBN Side)

### POST /api/digiemu/verify

Main boundary verification endpoint. Accepts a DigiEmu snapshot, computes its hash, verifies agent trust, and returns a signed result.

**Request:** DigiEmu canonical snapshot (JSON)  
**Response:** TBN verification result with signature

### POST /api/digiemu/hash

Compute the canonical hash of a snapshot. Used to verify both sides agree on the hash method.

**Request:** Any JSON object  
**Response:** `{ "snapshot_hash": "sha256:...", "method": "canonical_json_sha256" }`

### GET /api/digiemu/boundary/{agent_id}/{moment_id}

Look up a previous boundary verification result.

### GET /api/digiemu/status

Health check for the interoperability layer.

---

## Verification Flow

```
DigiEmu                          TBN
   │                              │
   │  1. Build snapshot           │
   │  2. Compute hash             │
   │                              │
   │──── POST /api/digiemu/verify ──→│
   │     (full snapshot)          │
   │                              │  3. Compute hash (must match)
   │                              │  4. Verify agent trust
   │                              │  5. Sign result
   │←── verification_result ──────│
   │                              │
   │  6. Compare hashes           │
   │  7. Validate signature       │
   │                              │
   ▼                              ▼
   PASS: Boundary proven          PASS: Trust verified
```

---

## Design Principles

1. **No system absorption** — TBN and DigiEmu remain independent
2. **Minimal shared surface** — only agent_id, moment_id, snapshot_hash
3. **Deterministic verification** — same input always produces same hash
4. **Cryptographic proof** — TBN signs its attestation with RSA-PSS
5. **Auditable** — all boundary verifications are logged
6. **Extensible** — schema versions allow future evolution

---

## Running the First Test

```bash
# Local test (server must be running on localhost:5004)
python test_digiemu_boundary.py

# Live test against production
python test_digiemu_boundary.py --live

# Custom URL
python test_digiemu_boundary.py --url https://tbn.hardinai.co.uk
```

---

## Next Steps

1. ✅ First boundary test — hash agreement + trust verification
2. Register DigiEmu test agents in TBN for full trust verification
3. DigiEmu validates TBN's RSA signature using public key
4. Bidirectional verification (TBN queries DigiEmu for snapshot confirmation)
5. Production agent registration and real decision-state tracking
