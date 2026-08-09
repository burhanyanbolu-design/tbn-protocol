TBN RECEIPT CONSTRUCTION SPECIFICATION
construction: tbn/receipt/1
=====================================

Status: FROZEN. This document defines a construction, not a field set. Once its
digest has been written into a signed receipt, this document MUST NOT be edited.
A change to the rules requires a new construction identifier and therefore a new
document with a new digest.

Publisher: Hardin Enterprises Ltd (trading as Hardin AI Solutions)
Licence: AGPL-3.0, published in the tbn-protocol repository so that the digest is
resolvable from any clone or mirror and does not depend on Hardin remaining
reachable.

0. HOW THIS DOCUMENT'S OWN DIGEST IS COMPUTED
---------------------------------------------
Read this first, because getting it wrong makes every other section
unverifiable.

    construction_spec = "sha256:" + SHA-256( this document, LF line endings )

The digest is computed over the file's bytes with all line endings normalised to
LF (0x0A). Any CR (0x0D) immediately preceding an LF is removed first. This is
the form git stores in its object database, and it is stated explicitly because a
checkout on Windows may materialise the file with CRLF, which yields a different
and wrong digest — the same file, 194 bytes longer.

No trailing-whitespace stripping, no encoding conversion, and no other
normalisation is applied. The file is UTF-8.

This section states a rule and deliberately does not state the resulting digest.
A document cannot contain its own hash.

WHY THIS DOCUMENT EXISTS
------------------------
A receipt previously carried `schema_version`, which names a FIELD SET. It does
not name the rules by which the receipt was canonicalised, hashed, chained or
signed. That gap produced a real failure: two different field sets shared the
label `tbn-receipt/2.1`, and a cutover defined as "the first receipt carrying
schema tbn-receipt/2.1" therefore also matched an earlier receipt, so a verifier
re-deriving the cutover from the stated rule got the wrong answer.

Naming a construction is not sufficient on its own either. A name can be
reinterpreted and a pointer can be repointed. Therefore a receipt carries BOTH
the name and the SHA-256 digest of this document. The name is for humans. The
digest is what makes the rules unreinterpretable: if these rules change, the
digest changes, and every receipt signed under the old digest remains
unambiguously bound to the old rules.

1. CANONICALISATION
-------------------
Canonical form of a JSON object is produced by, exactly:

    json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

That is: keys sorted lexicographically by Unicode code point at every level of
nesting; no whitespace anywhere, including none after ":" or ","; the result
encoded as UTF-8. No trailing newline. Non-ASCII characters are escaped as
Python's json module escapes them by default (ensure_ascii=True).

Numbers are serialised as the JSON module renders them. Implementations MUST NOT
reformat, pad, or change the precision of numeric values.

`null` is a value. A field present with value `null` is NOT the same as an absent
field, and the two produce different canonical bytes.

2. FIELD SET COVERED
--------------------
The receipt body, before hashing, contains these fields and no others:

    schema_version      string, the field-set label
    construction        string, "tbn/receipt/1"
    construction_spec   string, "sha256:<digest of this document>"
    merkle_construction string, the construction any Merkle root over these
                        receipts is to be computed under (see section 7)
    receipt_id          string, "tbn2_" + 32 lowercase hex characters
    key_id              string, "tbnkey_" + first 16 hex of SHA-256 of the
                        signing public key in PEM form
    agent_id            string
    action              string
    input_hash          string, SHA-256 hex of the input bytes
    output_hash         string, SHA-256 hex of the output bytes
    controls            array of objects, each {name, result, version,
                        version_hash}
    timestamp           string, ISO 8601 with explicit UTC offset
    prev_hash           string or null, see section 4
    chain_index         integer, see section 4
    rfc3161             object, see section 6
    run_id              string or null, an opaque caller-supplied identifier
                        grouping receipts minted during one run

`version_hash` within a control is the first 16 hex characters of the SHA-256 of
the UTF-8 encoding of the `version` string, or null when `version` is empty.

3. RECEIPT HASH
---------------
    receipt_hash = SHA-256( canonical(body) ) rendered as lowercase hex

where `body` is EXACTLY the field set in section 2. It does NOT include
`receipt_hash`, `algorithm`, or `signature`, because none of those exist at the
time it is computed.

4. CHAINING
-----------
`chain_index` is a non-negative integer, assigned strictly monotonically
increasing by one, starting at 0.

`prev_hash` is the `receipt_hash` of the receipt at `chain_index - 1`, or `null`
for `chain_index == 0`.

A chain is valid only if, for every receipt beyond the first, `prev_hash` equals
the immediately preceding receipt's `receipt_hash` AND `chain_index` is exactly
one greater. Gaps and repeats are invalid. There is no batch and no window: each
receipt is signed individually and inclusion is established by position in the
chain, not by membership of a set.

5. SIGNATURE
------------
    algorithm = "RSA-PSS-SHA256"

    signature = RSA-PSS(
        message   = canonical( body_with_receipt_hash_and_algorithm ),
        hash      = SHA-256,
        mgf       = MGF1 with SHA-256,
        saltLength = the maximum permitted for the key and hash
    )

rendered as lowercase hex.

The signed message covers the section 2 field set PLUS `receipt_hash` and
`algorithm`, and excludes only `signature` itself. Note that the salt length is
MAXIMUM, not the digest length; a verifier configured for a fixed salt length
will reject valid signatures.

RSA-PSS is randomised. Two signatures over identical bytes differ. A verifier
MUST verify, never compare signature bytes.

6. TIMESTAMPING
---------------
The `rfc3161` object is ALWAYS present. Its absence is never permitted and its
status is never implied.

    status  one of: anchored | not_requested | tsa_unavailable |
            tsa_rejected | tsa_timeout

When status is `anchored`, the object additionally carries the full RFC 3161
token base64-encoded, the exact SHA-256 hex imprint of the canonical body used as
the message imprint, the imprint algorithm ("sha256"), and the TSA certificate
chain in base64 DER.

A receipt whose status is anything other than `anchored` asserts an event time on
the issuer's own clock and nothing more. A verifier MUST NOT treat it as
independently timestamped.

7. MERKLE ROOTS OVER RECEIPTS
-----------------------------
This construction does not batch. Section 4 is the whole inclusion mechanism.
Where a Merkle root is nonetheless computed over a set of these receipts — for
reconciliation with a counterparty, or for anchoring — the following apply.

The `merkle_construction` field states which construction is to be used. A
verifier MUST read it and MUST NOT guess. Mixed values across a set are an error,
not something to resolve by majority.

Leaf ordering is by `chain_index` ascending. Ordering is part of the claim.

For `shango.merkle/rfc6962/v1`:

    leaf = SHA-256( 0x00 || canonical(receipt minus signature) )
    node = SHA-256( 0x01 || left || right )
    for n > 1, split at the largest power of two strictly less than n and
    recurse; the lone node is PROMOTED, never duplicated (RFC 6962 section 2.1)

For `shango.merkle/dup-last-count-bound/v1`:

    leaf and node as above, but an odd level DUPLICATES its last node. That
    construction is malleable across n (CVE-2012-2459), so the PUBLISHED value
    is not the raw root but:

    bound_root = SHA-256( 0x02 || n as uint64 big-endian || root as 32 raw bytes )

    n is the leaf count. The root is 32 RAW bytes, not its hex rendering. A
    decimal or hexadecimal encoding of n produces a different and invalid value.

Count binding is REQUIRED for the duplicate-last construction and NOT required
for RFC 6962, which has no cross-n collision to close.

8. WHAT A VALID SIGNATURE DOES AND DOES NOT ASSERT
--------------------------------------------------
A valid signature asserts that the issuer held the private key corresponding to
`key_id` and signed exactly these bytes.

It does not assert that the agent behaved correctly, that the action succeeded,
that the input or output was itself truthful, or — unless `rfc3161.status` is
`anchored` — that the stated time is independently attested.

9. VERIFICATION ORDER
---------------------
A verifier MUST fail closed at the first failure and MUST NOT continue.

    1. `construction` is recognised, and `construction_spec` matches the digest
       of the document the verifier holds. If it does not, STOP: the rules in
       force are not the rules being applied.
    2. Every field in section 2 is present. Absence is failure, not a default.
    3. `schema_version` is recognised.
    4. `receipt_hash` recomputes per section 3.
    5. `signature` verifies per section 5.
    6. Chain position is valid per section 4, where the neighbouring receipts are
       available.
    7. `rfc3161.status` is a recognised value; where `anchored`, the imprint
       matches the canonical body.

END OF SPECIFICATION
