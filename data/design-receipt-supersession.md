# Design — Receipt Supersession (TBN)

**Status:** design only. No code written. Written 12 August 2026.
**Reason it exists now rather than later:** the mechanism for correcting a
sealed artefact has to be designed *before* the first sealed error, not
improvised after it. We have already had the error — Register Entry 008, where
a mislabelled test put ten unauthorised receipts on the chain and they could
not be deleted. That was improvised. This is the designed version.

---

## 1. The problem, stated precisely

`api/tbn_memory.py` can correct itself. A contradicted fact is
**signed-superseded** with a stated reason (`supersedes` on the new shard),
the old shard is retained, and `recall()` hides it unless
`include_superseded=True`. Nothing is overwritten and nothing is lost.

`api/tbn_receipt_v3.py` cannot. The chain has `prev_hash` and `chain_index` and
nothing else: strictly append-only, no supersession semantics. If a receipt
asserts something later found to be false — a mislabelled construction, a
wrong input commitment, a control recorded as passed that never ran — a second
receipt can be issued but **nothing links the two and nothing marks the first
as unreliable.** The correction exists in the world and not in the chain.

Generalised (from the Shango exchange, 11–12 Aug 2026): sealing an artefact
buys integrity and charges for accuracy. It makes the record trustworthy and
makes correcting it expensive, so the pressure runs toward leaving a wrong
statement sealed rather than reopening it. Any sealed-record system therefore
needs a supersession mechanism designed in from the start.

---

## 2. The constraint that decides the shape

`api/tbn_construction.py` states the rule, and it was written *because* of
register item 17:

> A schema label MUST uniquely determine a field set. If two issuers emit
> different fields, they need different labels — never the same label with a
> footnote.

Current state: `CURRENT_SCHEMA = SCHEMA_2_3 = "tbn-receipt/2.3"`, with
`SCHEMA_FIELD_SETS` recording the mapping.

**Therefore an optional `supersedes` field on 2.3 is not available.** Adding a
field that is sometimes present would make one label describe two field sets —
recreating item 17 in the act of fixing something else. Supersession requires
**`tbn-receipt/2.4`** with its own entry in `SCHEMA_FIELD_SETS`.

---

## 3. The core design decision: additive, never mutative

**A superseding receipt must never modify, unsign, delete or invalidate the
receipt it supersedes.**

The old receipt stays byte-identical, stays signed, stays verifiable forever,
and remains a true record of *what was asserted at the time*. Supersession is a
**new signed assertion about a prior assertion** — not a mutation of it.

This is the same move as the Gate 2 erratum (`GATE2-ERR-001`) written the same
day: the sealed artefact was left untouched and a signed amendment quoted its
original wording verbatim. It pays neither cost — the seal survives and the
record becomes accurate.

Consequence: nothing about existing receipts, published Merkle roots, or the
anchor changes retrospectively. Supersession only ever *adds*.

---

## 4. Two classes of supersession, deliberately separated

Conflating these is how a correction mechanism becomes a rewrite capability.

### 4a. CORRECTION — additive, unilateral, low authority
> "Receipt X asserted P. P was wrong. Here is the corrected statement."

The original stays valid *as a record of what was asserted*. Nothing is
withdrawn. Any party may issue one about any receipt, including a counterparty
about ours — it is just a signed claim about a prior claim, and it stands or
falls on its own evidence.

### 4b. RETRACTION — subtractive, requires authority
> "Receipt X should not be relied upon."

This is the dangerous one. **If the issuer can unilaterally retract its own
receipts, TBN has a back door.** An attester able to quietly withdraw
inconvenient receipts is worse than one that cannot correct mistakes at all,
because the guarantee becomes conditional on the attester's goodwill — and that
is register **item 13's** problem exactly: authority and evidence in the same
hands.

So retraction carries its own state, reusing the three-state discipline adopted
for attribution on 11 Aug:

| `retraction_state` | Meaning |
|---|---|
| `counter_signed` | The other party signed the retraction too. Agreed. |
| `one_sided` | Only the issuer signed. Recorded, **not** treated as settled. |
| `disputed` | The counterparty signed a rejection of the retraction. |

Default is `one_sided`. A one-sided retraction is *asserted, not evidenced* —
Entry 002's shape — and must never render as "this receipt is invalid". It
renders as "the issuer asserts this receipt is unreliable; nobody else has
agreed."

**A verifier must therefore never silently drop a retracted receipt.** It
reports the retraction and its state, and lets the reader decide. Silent
dropping would let one party rewrite history by assertion.

---

## 5. Proposed field set for `tbn-receipt/2.4`

Additive to 2.3. Present only on receipts that supersede something; a normal
2.4 receipt without these fields is identical in shape to 2.3 — which means
**2.4 needs two entries in `SCHEMA_FIELD_SETS`, or the rule in §2 is broken
again.** Cleanest resolution: a supersession is its own artefact type.

```
supersedes            receipt_id of the receipt being superseded
supersession_class    "correction" | "retraction"
supersession_reason   free text, required, why
superseded_receipt_hash   the receipt_hash of the target, so the target is
                          bound by content and not merely by id
retraction_state      "counter_signed" | "one_sided" | "disputed"
                          (present only when class == "retraction")
counter_signature     the counterparty's signature over this body, when present
counter_signer_key_id which key signed it
```

`superseded_receipt_hash` matters: binding by `receipt_id` alone would let a
supersession point at an id whose content had been substituted. Bind the
content.

**RFC 3161 gives this for free and it is worth stating:** every receipt is
timestamped by an external TSA, so the *order* of receipt and supersession is
externally provable. Nobody can backdate a retraction.

---

## 6. Chain, roots and anchor semantics

Once supersessions exist, "all receipts" and "current receipts" are two
different sets. `tbn_memory` already solved this (`include_superseded`);
receipts need the same distinction, and because the anchor is **shared with
Shango** the choice must be agreed rather than assumed.

Recommendation:

- `verify_chain()` keeps validating the **full** append-only sequence. The
  chain is the history and history does not change. A superseded receipt is
  still a valid link.
- Merkle roots and the count-bound anchor continue to cover **all** receipts.
  Changing what a published root covers would retroactively alter the meaning
  of `d76019c6…`, `580ad28a…` and `4382b975…`.
- A **separate** derived view answers "what is current" — computed, never
  anchored, so no published root ever changes meaning.

---

## 7. What has to be agreed with Shango before any code

Not optional. Their verifier reads our signed body, `construction_of()` raises
rather than guessing, and the spec digest is bound into every receipt.

1. **The schema label** — `tbn-receipt/2.4` and its field set, so their verifier
   does not reject or misread it.
2. **Whether roots cover all or current receipts** (§6). Shared anchor.
3. **Whether retraction requires their counter-signature**, and the mechanics of
   obtaining it. This is the one with real consequences: if TBN both issues and
   retracts unilaterally, item 13's regress is concentrated rather than
   dissolved.
4. **The cutover date**, recorded rather than inferred from the first receipt
   carrying the new field — they asked for this explicitly for 2.3.

---

## 8. Code changes when the above is settled

- `api/tbn_construction.py` — add `SCHEMA_2_4`, its field set(s), bump
  `CURRENT_SCHEMA`. Single source of truth, so nothing else defines it.
- `data/spec-tbn-receipt-1.md` — revise to describe supersession, which
  **changes `CONSTRUCTION_SPEC`**. `issue_receipt(require_spec_match=True)`
  fails closed on spec drift, so the spec, its digest and the code must land
  atomically or issuance stops.
- `api/tbn_receipt_v3.py` — `issue_supersession()` as a distinct entry point,
  never a flag on `issue_receipt()`. `verify_receipt()` reports supersession
  status without acting on it. `verify_chain()` unchanged.
- A `current_view()` helper for §6.
- Permanent tests, per the standing discipline: a one-sided retraction must NOT
  render as invalid; a supersession must NOT alter the target's bytes or
  signature; the chain must still verify with supersessions present.

---

## 9. Sequencing — and the honest reason for it

This is architecture, not a customer request. The binding constraint remains
sales (Jenson gate). Three of the four decisions in §7 are joint and cannot be
made unilaterally.

So: **designed now, built when §7 is agreed.** Recorded as a decision with a
stated reason rather than left as an open gap — which is the whole point of
having the mechanism before the error rather than after it.
