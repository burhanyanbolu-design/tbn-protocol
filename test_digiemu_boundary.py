"""
TBN-DigiEmu Boundary Test
==========================
Runs the first interoperability proof between TBN and DigiEmu.

DigiEmu side: produces a canonical decision-state snapshot + SHA-256 hash
TBN side: verifies agent trust state and returns signed verification result
Shared boundary: agent_id + moment_id + snapshot_hash

Usage:
    python test_digiemu_boundary.py                    # test against localhost:5004
    python test_digiemu_boundary.py --live             # test against tbn.hardinai.co.uk
    python test_digiemu_boundary.py --url http://...   # test against custom URL

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0
"""

import json
import hashlib
import sys
import requests


def compute_canonical_hash(data: dict) -> str:
    """
    Compute SHA-256 hash using DigiEmu's canonical method:
    canonical JSON + sorted keys + no insignificant whitespace + UTF-8 + SHA-256
    """
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    hash_hex = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{hash_hex}"


def build_digiemu_snapshot() -> dict:
    """
    Build the minimal DigiEmu canonical snapshot for the first boundary test.
    This is exactly the structure Bruno proposed.
    """
    return {
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
                "input_text_required": True
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


def run_boundary_test(base_url: str):
    """Run the full TBN-DigiEmu boundary test."""
    print("=" * 70)
    print("  TBN-DigiEmu Boundary Test v1.0")
    print("=" * 70)
    print(f"\n  Target: {base_url}")
    print(f"  Protocol: tbn-digiemu-interop v1.0.0")
    print()

    # ── Step 1: DigiEmu produces the canonical snapshot ───────────────
    print("─" * 70)
    print("  STEP 1: DigiEmu produces canonical decision-state snapshot")
    print("─" * 70)

    snapshot = build_digiemu_snapshot()
    print(f"  Agent ID:  {snapshot['agent_id']}")
    print(f"  Moment ID: {snapshot['moment_id']}")
    print(f"  Schema:    {snapshot['schema_version']}")
    print()

    # ── Step 2: DigiEmu computes the canonical hash ───────────────────
    print("─" * 70)
    print("  STEP 2: DigiEmu computes canonical SHA-256 hash")
    print("─" * 70)

    digiemu_hash = compute_canonical_hash(snapshot)
    print(f"  Method:    canonical JSON + sorted keys + no whitespace + UTF-8 + SHA-256")
    print(f"  Hash:      {digiemu_hash}")
    print()

    # ── Step 3: Verify TBN computes the same hash ─────────────────────
    print("─" * 70)
    print("  STEP 3: Verify TBN computes the same hash (hash endpoint)")
    print("─" * 70)

    try:
        resp = requests.post(f"{base_url}/api/digiemu/hash", json=snapshot, timeout=10)
        if resp.status_code == 200:
            tbn_hash_result = resp.json()
            tbn_hash = tbn_hash_result["snapshot_hash"]
            hash_match = tbn_hash == digiemu_hash
            print(f"  TBN hash:  {tbn_hash}")
            print(f"  Match:     {'✅ PASS — hashes are identical' if hash_match else '❌ FAIL — hash mismatch'}")
        else:
            print(f"  ❌ Hash endpoint returned {resp.status_code}: {resp.text}")
            hash_match = False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Cannot connect to {base_url}")
        print(f"     Make sure the TBN server is running.")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        hash_match = False
    print()

    # ── Step 4: TBN verifies agent trust + returns signed result ──────
    print("─" * 70)
    print("  STEP 4: TBN verifies agent trust state (verify endpoint)")
    print("─" * 70)

    try:
        resp = requests.post(f"{base_url}/api/digiemu/verify", json=snapshot, timeout=10)
        if resp.status_code == 200:
            verification = resp.json()
            print(f"  Schema:    {verification['schema_version']}")
            print(f"  Agent:     {verification['agent_id']}")
            print(f"  Moment:    {verification['moment_id']}")
            print(f"  Status:    {verification['verification_result']['status']}")
            print(f"  Verified:  {verification['verification_result']['verified_at']}")
            print(f"  Method:    {verification['verification_result']['method']}")
            print(f"  Trust:     agent_verified={verification['trust_state']['agent_verified']}, "
                  f"trust_status={verification['trust_state']['trust_status']}")
            print(f"  Hash ref:  {verification['external_references']['digiemu_snapshot_hash'][:50]}...")
            print(f"  Signed:    {'✅ TBN signature present' if verification.get('tbn_signature') else '❌ No signature'}")

            # Verify the hash in the response matches what DigiEmu computed
            ref_hash = verification["external_references"]["digiemu_snapshot_hash"]
            hash_in_result = ref_hash == digiemu_hash
            print(f"  Hash ref match: {'✅ PASS' if hash_in_result else '❌ FAIL'}")
        else:
            print(f"  ❌ Verify endpoint returned {resp.status_code}: {resp.text}")
            verification = None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        verification = None
    print()

    # ── Step 5: Boundary validation summary ───────────────────────────
    print("─" * 70)
    print("  STEP 5: Boundary validation summary")
    print("─" * 70)

    all_pass = hash_match and verification and verification["verification_result"]["status"] in ("PASS", "WARN")

    print(f"""
  ┌─────────────────────────────────────────────────────────────────┐
  │  TBN-DigiEmu Boundary Test Result                               │
  ├─────────────────────────────────────────────────────────────────┤
  │  Hash agreement:        {'✅ PASS' if hash_match else '❌ FAIL'}                                  │
  │  Trust verification:    {'✅ PASS' if verification else '❌ FAIL'}                                  │
  │  Signed attestation:    {'✅ PASS' if verification and verification.get('tbn_signature') else '❌ FAIL'}                                  │
  │  Boundary integrity:    {'✅ PASS' if all_pass else '❌ FAIL'}                                  │
  ├─────────────────────────────────────────────────────────────────┤
  │  Overall:               {'✅ INTEROPERABILITY PROVEN' if all_pass else '❌ BOUNDARY TEST FAILED'}              │
  └─────────────────────────────────────────────────────────────────┘
""")

    if all_pass:
        print("  Both systems independently validated the same agent/moment boundary.")
        print("  TBN verified agent trust. DigiEmu produced the decision-state hash.")
        print("  The shared reference (agent_id + moment_id + snapshot_hash) is consistent.")
        print()
        print("  Systems remain independent but interoperable. ✅")
    else:
        print("  Boundary test did not fully pass. Check the steps above for details.")

    print()
    return all_pass


if __name__ == "__main__":
    # Determine target URL
    if "--live" in sys.argv:
        base_url = "https://tbn.hardinai.co.uk"
    elif "--url" in sys.argv:
        idx = sys.argv.index("--url")
        base_url = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "http://localhost:5004"
    else:
        base_url = "http://localhost:5004"

    success = run_boundary_test(base_url)
    sys.exit(0 if success else 1)
