"""
TBN construction identity — THE single source of truth
======================================================
Every module that issues or verifies a TBN receipt imports its construction
identity from here. Nothing defines these values locally.

WHY THIS MODULE EXISTS
----------------------
Disagreement Register item 17: two receipt-issuing modules
(`tbn_receipt_v2.py` and `tbn_receipt_v3.py`) both declared
`SCHEMA_VERSION = "tbn-receipt/2.1"` while emitting DIFFERENT field sets
(`tsa_anchored` boolean vs a full `rfc3161` object). That broke the SB 942
cutover definition: "the first receipt carrying schema tbn-receipt/2.1" was
pinned at chain_index 3952 but also matched 3335, eight days earlier, so a
verifier re-deriving the cutover from the published rule got the wrong answer.

The defect was not the labels. It was that each module owned its own copy of a
value that had to agree across all of them. Fixing the labels without removing
the duplication leaves the same defect available to the next person.

So: ONE definition, imported. A future module that invents its own constants is
the bug, and reviewers should treat it as one.

THE RULE THIS MODULE ENFORCES
-----------------------------
A schema label MUST uniquely determine a field set. If two issuers emit
different fields, they need different labels — never the same label with a
footnote.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""
import hashlib
import os

# ── Construction identity ─────────────────────────────────────────────
# `construction` names the rules. `construction_spec` binds their CONTENT by
# digest, because a name can be reinterpreted and a pointer can be repointed.
# If the rules change the digest changes, and every receipt signed under the old
# digest stays unambiguously bound to the old rules — the property a bare
# `schema_version` lacked.
#
# Agreed with Shango 7 Aug 2026: the string is theirs to accept (they did), the
# digest is ours to produce (this is it).
CONSTRUCTION = "tbn/receipt/1"
CONSTRUCTION_SPEC = "sha256:08d6fb20645ba9357c1a3e87debc71bbb7d141521859e2ed001613c7d5077df7"
CONSTRUCTION_SPEC_PATH = "data/spec-tbn-receipt-1.md"

# Which construction a Merkle root over these receipts is computed under. Read
# by Shango's construction_of(), which raises rather than guessing, so this must
# be a value their verifier knows.
#
# NOTE — JOINT DECISION NOT YET FORMALLY AGREED. We emit Shango's published
# identifier because their verifier is the only consumer today, and because two
# names for one construction is precisely the ambiguity both sides are removing.
# Our own tbn/merkle/1 is byte-identical, verified for n=1..129 against the
# RFC 6962 section 2.1 reference (api/test_merkle_construction.py).
MERKLE_CONSTRUCTION = "shango.merkle/rfc6962/v1"
MERKLE_CONSTRUCTION_EQUIVALENT = "tbn/merkle/1"

# ── Schema labels ─────────────────────────────────────────────────────
# Each label maps to exactly ONE field set. Recorded here so the mapping is
# checkable rather than folklore.
SCHEMA_2_0 = "tbn-receipt/2.0"   # historical
SCHEMA_2_1 = "tbn-receipt/2.1"   # historical: tsa_anchored bool, no rfc3161 object
SCHEMA_2_2 = "tbn-receipt/2.2"   # historical: full rfc3161 object, no construction fields
SCHEMA_2_3 = "tbn-receipt/2.3"   # current: full rfc3161 object + construction identity + run_id

CURRENT_SCHEMA = SCHEMA_2_3

SCHEMA_FIELD_SETS = {
    SCHEMA_2_0: "original v2 body; no tsa_anchored, no rfc3161 object",
    SCHEMA_2_1: "adds tsa_anchored boolean on every receipt; no rfc3161 object retained",
    SCHEMA_2_2: "replaces tsa_anchored with a full rfc3161 object incl. token_b64 + imprint",
    SCHEMA_2_3: ("adds construction, construction_spec, merkle_construction and "
                 "run_id to the SIGNED body; rfc3161 object as in 2.2"),
}

SUPPORTED_SCHEMAS = (SCHEMA_2_0, SCHEMA_2_1, SCHEMA_2_2, SCHEMA_2_3)

# Fields that exist only from 2.3. Absent in earlier receipts, which is correct
# and not a failure — but REQUIRED from 2.3, because a construction identifier
# that can be omitted is not an identifier.
CONSTRUCTION_FIELDS = ("construction", "construction_spec",
                       "merkle_construction", "run_id")


def spec_digest_from_disk(path: str = None) -> str:
    """Digest of the frozen spec, normalising CRLF to LF per section 0 of that
    document. LF because that is what git stores; a Windows checkout materialises
    CRLF and hashes to a different, wrong value — 194 bytes longer for the same
    file."""
    p = path or CONSTRUCTION_SPEC_PATH
    with open(p, "rb") as f:
        raw = f.read()
    return "sha256:" + hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def verify_spec_digest(path: str = None) -> dict:
    """Confirm the frozen spec on disk still matches the digest we sign into
    receipts. Without this, FROZEN is a comment rather than a property: an edit
    would silently change the rules every existing receipt claims to follow, and
    nothing would notice.

    Returns a dict rather than raising, so issuance can treat a mismatch as fatal
    while a reporting tool can report it and continue."""
    try:
        actual = spec_digest_from_disk(path)
    except FileNotFoundError:
        return {"ok": False, "reason": "spec_file_missing",
                "expected": CONSTRUCTION_SPEC,
                "path": path or CONSTRUCTION_SPEC_PATH,
                "note": "The spec is published in the repo so its digest resolves "
                        "from any clone. Missing here means a verifier cannot check "
                        "the rules this receipt claims to follow."}
    if actual != CONSTRUCTION_SPEC:
        return {"ok": False, "reason": "spec_digest_mismatch",
                "expected": CONSTRUCTION_SPEC, "actual": actual,
                "note": "The frozen spec has been edited. That retrospectively "
                        "changes the rules every existing receipt claims. Revert "
                        "it, or issue a NEW construction identifier and a new "
                        "document."}
    return {"ok": True, "digest": actual}


def construction_fields(run_id=None) -> dict:
    """The construction-identity block to merge into a receipt body. One call
    site, so no issuer can drift.

    `run_id` is present and explicitly null when unset rather than omitted:
    absence and null are different canonical bytes, and the spec says so."""
    return {
        "construction": CONSTRUCTION,
        "construction_spec": CONSTRUCTION_SPEC,
        "merkle_construction": MERKLE_CONSTRUCTION,
        "run_id": run_id,
    }
