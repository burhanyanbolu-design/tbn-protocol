"""
TBN Protocol — v2 Governance API (Hardened Attestation Layer)
=============================================================
Public HTTP endpoints for the v2 receipt: schema_version, key_id, hash chain
(prev_hash + chain_index), control result + version(+hash), optional RFC 3161
timestamp, RSA-PSS-SHA256 signature.

POST /api/v2/attest   — submit a decision for attestation (client commitments honoured)
POST /api/v2/verify   — standalone verify a v2 receipt (public key only, no trust)
GET  /api/v2/health   — service status

Auth: Authorization: Bearer <api_key>   (same key store as v1)

Client-supplied `input_hash` / `output_hash` are honoured VERBATIM as commitments,
so the caller's authorisation-envelope binding (e.g. SHA-256(canonical(envelope)))
is exactly what gets signed — not a server re-hash. controls[] are honoured as sent
(including version_hash) so a third party can recompute and reach the same values.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""
import os
import json
from flask import Blueprint, request, jsonify

from .v1_governance import require_v1_auth

# ISSUER SWITCHED 7 Aug 2026: tbn_receipt_v2 -> tbn_receipt_v3.
#
# WHY. Register item 8 requires the construction identifier to be inside the
# SIGNED body, and item 7 requires a run_id so a run that ends abnormally can be
# enumerated. Both live in v3. Adding them to v2 as well would mean two modules
# emitting overlapping field sets from duplicated constants — which is precisely
# how item 17 (two modules both declaring schema tbn-receipt/2.1 with different
# fields) happened. One issuer, one schema label, one definition.
#
# WHAT HAD TO BE FIXED FIRST. v3's issue_receipt() did not accept verbatim
# input_hash / output_hash, so switching to it would have silently replaced a
# caller's own commitment (e.g. SHA-256(canonical(envelope))) with a server
# re-hash — breaking the contract this endpoint publishes, with no error raised.
# Verbatim passthrough was added to v3 before this switch.
#
# tbn_receipt_v2 is retained as the HISTORICAL issuer. Receipts it produced stay
# valid and are not relabelled. Do not issue new receipts through it.
from . import tbn_receipt_v3 as _v2

v2_governance = Blueprint("v2_governance", __name__, url_prefix="/api/v2")

V2_RECEIPTS_DIR = "data/v2_receipts"


def _persist(receipt: dict):
    os.makedirs(V2_RECEIPTS_DIR, exist_ok=True)
    rid = receipt.get("receipt_id")
    if rid:
        with open(os.path.join(V2_RECEIPTS_DIR, f"{rid}.json"), "w") as f:
            json.dump(receipt, f, indent=2)


@v2_governance.route("/attest", methods=["POST"])
@require_v1_auth
def v2_attest():
    """Issue a v2 receipt. Accepts:
       { agent_id, action, input_hash?, output_hash?, input?, output?,
         controls:[{name,result,version,version_hash?}], timestamp? }
       If input_hash/output_hash are supplied they are signed verbatim."""
    b = request.get_json(silent=True) or {}
    agent_id = b.get("agent_id")
    action = b.get("action")
    if not agent_id or not action:
        return jsonify({"error": "agent_id and action are required"}), 400
    try:
        receipt = _v2.issue_receipt(
            agent_id,
            action,
            input_data=b.get("input", ""),
            output_data=b.get("output", ""),
            controls=b.get("controls"),
            timestamp_authority=bool(b.get("timestamp", False)),
            input_hash=b.get("input_hash"),
            output_hash=b.get("output_hash"),
            # Optional. When supplied it is signed into the body, which is what
            # makes /api/v2/run/<run_id> able to enumerate a run that died.
            run_id=b.get("run_id"),
        )
        _persist(receipt)
        return jsonify(receipt)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@v2_governance.route("/verify", methods=["POST"])
def v2_verify():
    """Verify a v2 receipt against the published public key. No server trust needed."""
    b = request.get_json(silent=True) or {}
    receipt = b.get("receipt") or b
    return jsonify(_v2.verify_receipt(receipt))


@v2_governance.route("/health", methods=["GET"])
def v2_health():
    n = 0
    if os.path.isdir(V2_RECEIPTS_DIR):
        n = len([x for x in os.listdir(V2_RECEIPTS_DIR) if x.endswith(".json")])
    return jsonify({
        "status": "ok",
        "schema_version": _v2.SCHEMA_VERSION,
        "v2_receipts_stored": n,
    })


# ══════════════════════════════════════════════════════════════════════
# RUN-SCOPED ENUMERATION — Disagreement Register item 7
# ══════════════════════════════════════════════════════════════════════
# THE PROBLEM (Shango's words): "If a run ends abnormally we cannot enumerate
# what was minted in our name."
#
# WHY PER-PARTNER IS NOT ENOUGH: /api/v1/audit/partner/<name> returns everything
# ever minted under a name. Slicing that to one run means slicing by TIMESTAMP —
# and timestamps are exactly what we argued should not be trusted for ordering,
# because they can collide or move backwards. Applying our own argument one layer
# out: scope by the monotonic value that is already inside the signed body.
#
# WHY THE RANGE CANNOT BE THE MEMBERSHIP DEFINITION: the receipt chain is GLOBAL.
# One chain file, one head, one count, across every agent and every partner. So a
# chain_index range covering one run has other partners' receipts interleaved
# inside it. Membership is therefore defined by `run_id`; the index range is
# reported ALONGSIDE as metadata describing the window, never as its contents.
# Handing back a range and letting the caller assume everything in it is theirs
# would be a correctness bug with no way for them to detect it.
#
# Auth is required: a run's contents are the caller's data, not public.

def _load_v2_receipts():
    """Every persisted v2 receipt, ordered by chain_index ascending.

    Receipts with no chain_index are returned separately rather than guessed at,
    because ordering is part of the claim."""
    ordered, unordered = [], []
    if not os.path.isdir(V2_RECEIPTS_DIR):
        return ordered, unordered
    for fn in os.listdir(V2_RECEIPTS_DIR):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(V2_RECEIPTS_DIR, fn)) as f:
                r = json.load(f)
        except Exception:
            continue
        (ordered if isinstance(r.get("chain_index"), int) else unordered).append(r)
    ordered.sort(key=lambda r: r["chain_index"])
    return ordered, unordered


def _window(receipts):
    """Index range for a set of receipts, as METADATA about the window.

    DELIBERATELY DOES NOT REPORT "gaps" OR "contiguous".

    An earlier version did, and a test showed why that was actively dangerous.
    The receipt chain is GLOBAL across every agent and partner, so the indices
    belonging to any one run are almost never consecutive — other parties mint in
    between. A "gaps" field would therefore be non-empty for essentially every
    real run, and a counterparty enumerating a run that died would read those
    gaps as RECEIPTS MISSING FROM THEIR RUN. That is the exact wrong inference,
    in the exact situation this endpoint exists to serve.

    Index gaps carry no information about completeness on a shared chain.
    Completeness cannot be established from indices at all: it requires knowing
    how many receipts the run was supposed to produce, which only the caller
    knows. So this reports what is true — the range, the count, and how much of
    the range belongs to other parties — and says plainly what it cannot tell you.
    """
    idx = [r["chain_index"] for r in receipts]
    if not idx:
        return {"first_chain_index": None, "last_chain_index": None,
                "span": 0, "count": 0, "indices_belonging_to_others": 0,
                "note": "No indexed receipts for this run."}
    span = idx[-1] - idx[0] + 1
    return {
        "first_chain_index": idx[0],
        "last_chain_index": idx[-1],
        "span": span,
        "count": len(idx),
        "indices_belonging_to_others": span - len(idx),
        "note": ("The chain is GLOBAL across all agents and partners, so this "
                 "range also contains receipts belonging to others — see "
                 "indices_belonging_to_others. Membership of this run is defined "
                 "by run_id, never by the range. Non-consecutive indices within a "
                 "run are EXPECTED and are NOT evidence of a missing receipt. "
                 "This endpoint cannot tell you whether the run is complete; only "
                 "you know how many receipts it should have produced. Compare "
                 "`count` against that."),
    }


@v2_governance.route("/run/<run_id>", methods=["GET"])
@require_v1_auth
def v2_run(run_id):
    """Enumerate everything minted under one run_id.

    Query params:
      include=bodies   return full signed receipt bodies, not just ids
    """
    ordered, unordered = _load_v2_receipts()
    mine = [r for r in ordered if r.get("run_id") == run_id]
    mine_unordered = [r for r in unordered if r.get("run_id") == run_id]

    # Receipts predating the run_id field cannot be attributed to any run. Say so
    # explicitly rather than let a caller read an empty result as "nothing was
    # minted" when the truth may be "we cannot tell".
    legacy = sum(1 for r in ordered if "run_id" not in r)

    out = {
        "run_id": run_id,
        "count": len(mine) + len(mine_unordered),
        "receipt_ids": [r.get("receipt_id") for r in mine],
        "window": _window(mine),
        "receipts_without_chain_index": len(mine_unordered),
        "receipts_predating_run_id_field": legacy,
        "merkle_construction": None,
        "verify_each_at": "/api/v2/verify",
    }

    if legacy and not out["count"]:
        out["warning"] = (
            f"No receipts carry this run_id, and {legacy} stored receipt(s) predate "
            f"the run_id field entirely. An empty result here does NOT mean nothing "
            f"was minted — for those receipts the run cannot be determined. Use "
            f"/api/v1/audit/partner/<name> and reconcile by chain_index.")

    if mine:
        # A root over the run, with the construction named. Emitted from the
        # receipts' own signed merkle_construction where present, never guessed;
        # mixed values are an error rather than something to resolve by majority.
        constructions = {r.get("merkle_construction") for r in mine}
        constructions.discard(None)
        if len(constructions) > 1:
            out["merkle_error"] = (
                f"mixed merkle_construction across this run: {sorted(constructions)}. "
                f"Refusing to compute a root — a root is only meaningful under one "
                f"construction.")
        else:
            out["merkle_construction"] = (constructions.pop() if constructions
                                          else "unstated_in_receipt_body")
            out["merkle_leaf_order"] = "chain_index ascending"
            out["merkle_note"] = (
                "Leaf and root computation is defined by the construction named "
                "above; see data/spec-tbn-receipt-1.md section 7. This endpoint "
                "states membership and ordering, which is what a root needs.")

    if request.args.get("include") == "bodies":
        out["receipts"] = mine + mine_unordered

    return jsonify(out)


@v2_governance.route("/runs", methods=["GET"])
@require_v1_auth
def v2_runs():
    """Every run_id we hold, with its window. Lets a counterparty find the run
    that died without knowing its identifier in advance."""
    ordered, unordered = _load_v2_receipts()
    runs = {}
    for r in ordered:
        rid = r.get("run_id")
        if rid:
            runs.setdefault(rid, []).append(r)
    return jsonify({
        "runs": [{"run_id": k, "count": len(v), "window": _window(v)}
                 for k, v in sorted(runs.items())],
        "run_count": len(runs),
        "receipts_predating_run_id_field": sum(1 for r in ordered if "run_id" not in r),
        "receipts_without_chain_index": len(unordered),
        "note": ("run_id was added to the signed body in schema tbn-receipt/2.3. "
                 "Receipts issued before that carry no run_id and cannot be "
                 "attributed to a run retrospectively — attributing them after the "
                 "fact would be a guess, and a guess in an evidence store is worse "
                 "than an absence."),
    })
