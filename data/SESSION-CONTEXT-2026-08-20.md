# SESSION CONTEXT — 20 August 2026

Handoff doc. Continues from `data/SESSION-CONTEXT-2026-08-19.md` (CV rewrite, HN
post draft, hardinai.co.uk SEO/GA fixes). This session did three things: shipped
two governance features prompted by a LinkedIn comment, ran Area Five Stage
Sixteen to a completed honest failure, and made Elastic Hippocampus pilot-ready.

All work is committed and pushed. Two repos:
- `tbn-protocol` → `origin/main` at `35500d2`
- `hardinai.co.uk` site → `origin/main` at `7da3d33`

---

## 1. GEORGE PETROVSKY'S COMMENT → TWO REAL FIXES SHIPPED

A LinkedIn commenter (entrepreneur, 67-person eng company) raised two genuine
gaps in the "no receipt, no effect" doctrine. Both were real, verified against
the actual code, and both are now fixed and live.

**Gap 1 — authority vs informed authority.** A receipt proved *who* approved,
but not *what they saw*. In a multiplayer session where state accumulates from
other participants' turns, someone can authorise an action against context they
never watched build. `approve_policy()` took an `approver` string and nothing else.

**Gap 2 — refusals were a dead end.** A hard refusal mid-flow left no durable
record, so the pressure valve is people doing it manually off-session. Result: a
clean audit trail of safe actions and silence on the consequential ones.

**What was built** (`api/tbn_memory_tiers.py`, wired through `memory_service.py`,
`health_agent.py` routes, and `api/sdk/hardin_memory.py`):

- `approve_policy()` / `reject_policy()` now accept `rendered_context`, hash it
  into `approval_context_hash`, and record `informed_context_captured`. Omitting
  it still works but honestly flags `false` rather than pretending.
- New `log_refusal()` / `record_followup()` / `get_refusals()`. Refusals are
  signed append-only shards; follow-ups are separate shards joined by
  `refusal_id`, so a refusal can never be quietly erased once overridden.
  `get_refusals()` surfaces `followup_pending: true` for anything unresolved —
  that is the "silence on the consequential ones" gap made visible.
- New routes: `POST /v1/memory/refusals`, `POST /v1/memory/refusals/followup`,
  `GET /v1/memory/refusals`. Plus matching SDK methods.

Verified 19/19 locally, deployed via SCP to Lightsail, service restarted, then
exercised against the live HTTPS API end-to-end (refusal logged, follow-up
recorded, `followup_pending` flipped, real `approval_context_hash` returned).
Backward compatible — existing callers unaffected.

**Made visible in the demos.** First added to `api/templates/memory_demo_bot.html`
(the `/memory/demo/support-bot` page), then Burhan corrected that it belonged on
the public landing page. Added to `demo/hardinai-site/multiplayer.html`: the
Alice/Bob illustrative session now has clickable `🔏 approval_context_hash`,
`🚫 refusal logged`, and `↩ followup recorded` markers, plus two new rows in the
"No Receipt, No Effect" trust section. All clearly labelled synthetic, matching
the page's existing honesty disclaimers. Verified with a Node DOM-shim smoke test
(12/12, including the pending→resolved transition) before pushing. Live and
confirmed by direct HTTPS fetch.

---

## 2. AREA FIVE STAGE SIXTEEN — COMPLETED, `HELD_OUT_FAIL` 15/17

Area Five = Elastic Hippocampus = the memory product. Same thing, three names.

**Found at session start:** five orphaned `stage16_*.py` scripts, untracked,
timestamped earlier that day — a session that crashed mid-build. `stage16_evaluate.py`
was missing and there was no preregistration. No corpus had been acquired, so
nothing was contaminated.

**Governance problem flagged before doing anything.** The Stage Fifteen
preregistration says Fifteen was final, and the Area Five conclusion says *"No
Stage Sixteen or further automatic confirmation loop will be started"* — but it
permitted a **separately authorized study** meeting three conditions. Burhan
authorized it as that. The preregistration records honestly that it meets two
(corpus-size feasibility check now exists; label tooling immutable and exclusive)
and **fails the third** (labels are still machine-pooled, not independent human
judgment).

**Written this session:**
- `demos/elastic-hippocampus-proof/stage16_evaluate.py` — the missing sixth
  script, adapted from Stage 15 with every binding corrected to 16 (stage number,
  `stage16-candidate|` domain, `sealed_stage16_flat_global_top30` provenance,
  corpus/lock/result paths). Retains `O_EXCL` everywhere, review-before-pool so a
  partial review is preserved not retried, score lock created *before* the single
  evaluator join, exactly-17-gates assertion.
- `data/elastic-hippocampus-stage-sixteen-preregistration-2026-08-13.md` — frozen,
  all 8 script hashes verified machine-readable by the parsing regex, all 10
  prior-evidence bindings verified hash-matching.

**Disclosures written in before acquisition, deliberately so they could not be
dropped afterwards:** multiple-comparisons position (this is the 5th held-out
attempt against the same `Recall@5 >= 0.60` gate, so a pass carries less weight
than a first-attempt pass); `body_max` outlier-sensitivity with RFC 3261 being
much larger than the other five sources; and `q12` referencing DNS inside a DKIM
question as the single risky wording.

**Run:** 6 RFCs acquired (1,320,338 bytes), preflight gave **918 chunks** — clears
the 400-floor that killed Stage Fifteen at 381. Predictions sealed, blind pool
built, blind sub-agent adjudicated reading only the review file, labels frozen,
scored once.

**Result: `HELD_OUT_FAIL`, 15/17 gates.**

| Method | Cand. recall | Recall@5 | nDCG@5 | MRR | Hit@5 | Ctl nonempty | Routing work |
|---|---:|---:|---:|---:|---:|---:|---:|
| Area Five indexed | 0.897 | 0.373 | 0.638 | 0.771 | 15/16 | 1/4 | **85** |
| Area Five scan | 0.897 | 0.373 | 0.638 | 0.771 | 15/16 | 1/4 | 1041 |
| Flat scan | 0.869 | 0.386 | 0.630 | 0.724 | 15/16 | 1/4 | 918 |

**Gate 9 failed — Recall@5 0.373 vs >= 0.60.** But flat scan also failed at 0.386,
and flat is the exhaustive ceiling. The gate is very likely unsatisfiable: the
adjudicator marked 154 relevant chunks over 16 queries (mean 9.6, q16 got 19), and
against a top-5 budget a 19-relevant query caps at 5/19 = 0.263. The dense-label
ceiling was declared in advance and was NOT used to retune anything.

**Gate 15 failed — control `q20` did not abstain.** Coverage was exactly
`0.750000` against a `>= 0.75` threshold — cleared by zero margin because six of
eight tokens (`condition`, `defines`, `hand`, `perfect`, `extensive`, `game`) are
ordinary English words present in networking RFCs. Only `trembling` and
`equilibrium` were absent. **This was predicted from the sealed label-free
predictions and reported to Burhan before scoring**; he chose to proceed rather
than abort. All three methods including flat failed identically, so the defect is
in the shared abstention rule, not Area Five routing.

**THE LOAD-BEARING WIN: routing is fixed, confirmed on untouched data.**
Stage Twelve failed q01/q03 by routing DNS questions to the wrong RFCs because
the router read only titles/headings. Stage Thirteen's `body_max` fixed it but on
already-observed labels. Stage Sixteen confirms it on a corpus never seen:
**16/16 positive queries routed to their frozen expected artifact**, including
the flagged `q12`. Plus 10.8× routing-work reduction, exact scan/index parity,
zero integrity/provenance/determinism failures, and Area Five above flat on
candidate recall, nDCG@5, and MRR.

**Two defects recorded as findings, NOT repaired** — the one-attempt and
no-tuning rules bind after acquisition:
1. Boundary-fragile abstention (`>= 0.75` should be strict `>` or need a minimum
   absolute count of known content terms).
2. A likely unsatisfiable quality gate (needs a metric whose achievable maximum
   isn't capped below its own threshold).

Per the stopping rule, **no Stage Seventeen.** Report at
`data/elastic-hippocampus-stage-sixteen-report-2026-08-13.md` with sha256 sidecar.
Committed as `f671872`.

**IMPORTANT — do not "fix" the frozen scripts.** The `0.75` threshold lives only
in `stage*_retrieval.py`, which are hash-bound in the preregistration and
committed immutable. Editing them to fix a defect they just revealed is exactly
the failure mode the protocol exists to prevent. Production has no coverage gate
at all; its abstention lives in the authority layer and passes
`unknown_subject_abstention` in the pilot.

---

## 3. ELASTIC HIPPOCAMPUS MADE PILOT-READY (commit `35500d2`)

**Discovery:** EH is *already integrated* into live Hardin Memory as a
non-authoritative shadow router (`api/area_five_shadow.py`). Its own docstring:
*"This index is never authoritative... Hardin reauthorizes, reloads, verifies,
and ranks every candidate before any memory text is returned."* In
`memory_service.recall()` EH narrows candidates → Hardin re-verifies and ranks →
falls back to full authoritative recall if EH yields nothing, recording
`authority_fallback`. Fail-open by design. **It was switched off in production.**

That architecture matches the Stage Sixteen evidence exactly: EH's measured
strength is *narrowing* (16/16 routing, 10.8× less work), its measured weakness is
*being the final ranker* (Recall@5 below flat). The shadow design uses it only for
narrowing.

**Problem found:** `enabled()` read one process-wide env var, so arming the router
on a shared instance applied it to **every tenant at once**. A bounded pilot was
impossible — smallest blast radius was all customers.

**Fix shipped:** `enabled()` now takes an optional principal and honours
`AREA_FIVE_SHADOW_TENANTS`, a comma-separated allowlist. Unset/empty = all tenants
(original behaviour preserved). **Fails CLOSED** — allowlist configured but no
principal supplied means the router stays off. Both call sites in
`memory_service.py` (`_shadow_sync`, `recall`) now pass the principal.

Verified before deploying: 17/17 allowlist unit checks (master-switch precedence,
backward compat, fail-closed paths, whitespace/empty parsing); 9/9 scoped recall
checks proving two tenants in one process take different paths, the
non-allowlisted one silently hitting authority fallback with
`sync_status: disabled`, both still returning correct content, roles swapping when
the allowlist changes; existing `demos/area-five-shadow-pilot/pilot.py` still
**24/24**, no regression.

Deployed to Lightsail, service restarted, `memory.hardinai.co.uk` returning 200.
**Production behaviour unchanged** — `AREA_FIVE_SHADOW_ENABLED` is still unset, so
EH remains off. This only makes a scoped pilot possible.

**To start the pilot,** add a systemd drop-in:
```
AREA_FIVE_SHADOW_ENABLED=1
AREA_FIVE_SHADOW_TENANTS=ten_<one_real_tenant_id>
```
Then watch `authority_fallback` and `routing_work` in that tenant's recall traces.
Deliberately not done — choosing which real customer to expose is Burhan's call.

---

## 4. POSITIONING CONCLUSIONS REACHED

**What EH is for:** situations where "the AI said so" isn't good enough and you
must prove what it knew and why. Not better search — flat scan beat it on top-5
recall, and it has no semantic/neural understanding. Vector DBs (Pinecone,
Weaviate, Chroma) win on semantic recall but cannot say which stored fact drove an
answer, prove nobody tampered with it, hold contradicting claims with attribution,
or refuse when out of depth. EH does all four.

**Lead with efficiency, provenance, and abstention. Never lead with accuracy.**

Buyers: regulated AI deployments (EU AI Act, California SB 942 — already sold into
via TBN Sentinel), financial services/insurance (auditable declines), healthcare
and legal (contradiction retention matters), any agent touching money or
irreversible actions.

**Hardin Filter relationship — different layer, but EH is its missing backend.**
Filter checks what the AI *said* (G8–G16 output checks). EH manages what it
*knows*. Three specific fits:
- **G15 `check_approved_source(answer_text, trusted_sources=None)`** already takes
  a trusted-source list that's currently hand-supplied. EH *is* a signed,
  provenance-tracked, tamper-evident source store. Near drop-in. Strongest fit.
- **G8 source attribution** currently fetches live to verify sources. EH gives a
  local pre-verified signed store — faster, no network, and can prove the source
  hasn't changed since verification.
- **G16 known entity claims** verifies against authoritative facts, which is
  exactly Tier-1 signed facts.

Combined claim upgrade: Filter today says "this citation exists." With EH behind
it: "this citation exists, here is the signed record we verified it against, when,
and proof nobody altered it since."

**Do NOT merge the codebases.** Keep Filter as the output-check engine and EH as
the evidence store, connected via an interface. Fusing them loses what makes
Filter sellable standalone — a browser/editor extension needing no memory
infrastructure.

---

## 5. EOG / CHEBYSHEV — HONEST NOVELTY POSITION

Burhan asked whether his grid formula was already known. Checked via web search
(directional only — **not** a formal prior-art search).

**The combined scheme has two separable parts:**
1. **Distance formula `max(|Δrow|, |Δcol|)` — this is exactly Chebyshev distance.**
   Not similar, identical. Independently derived, not copied, but it is not new
   math. Standard in chess engines, warehouse robotics, image processing, CNC
   motion. Worked example confirmed: 19→36 on an 8-wide grid is 4 moves
   (`max(3,4)`), which is what his diagram already showed.
2. **The addressing/seam-identification rule** (`L(r,c) = (n-1)r + c` with the last
   cell of a row *identified* with the first of the next) — no prior-art match
   found. Closest relative is HPC halo/ghost cells, but those **duplicate**
   boundary data for parallel reads whereas this **merges** it to eliminate
   duplicate-write hazard. Different design point, not an improvement on halo
   cells and not the same thing.

**Patent position:** pure math generally isn't patentable in UK/EU/US (UK Patents
Act excludes mathematical methods "as such"; US Alice/Mayo). So no patent concern
on the bare formula, and no publish-before-file risk for it. A specific technical
application could differ — that needs a patent attorney, not this session.

**Trade-secret vs publish tension discussed.** A patent *is* public disclosure in
exchange for a monopoly, so "patent it but keep it secret" isn't an option.
Recommendation given: don't publish the addressing mechanism, don't file yet
either — file only becomes worth the cost once there's a validated performance
advantage, which the held-out record does not yet support. Market on outcomes, not
mechanism. Area Five ownership is not in question; his own docs already draw the
right line, claiming originality in the *arrangement* while stating "no novelty
claim has been established" for the shared math.

---

## 6. STANDING NOTES

- **PowerShell here mangles inline `-Command` strings** with nested quotes and `$`
  variables. Confirmed again this session — write to a file and `Get-Content` it,
  or use `Out-File` then read back. Long `git push` output also truncates oddly;
  `--quiet` plus a follow-up `git log` is more reliable.
- **Two separate git repos.** `demo/hardinai-site` tracks the live GitHub Pages
  site (`hardinai.co.uk`); the parent tracks `tbn-protocol`. Always `git fetch`
  before pushing the site repo — it has diverged before. GitHub Pages took ~60–90s
  to propagate this session, and an early check gave a false negative; verify
  against `raw.githubusercontent.com` first to separate "push failed" from "CDN
  lag."
- **`api/` has hundreds of untracked one-off scripts.** Never `git add .` there.
  Stage only the files actually changed.
- **Lightsail deploy is SCP + `sudo systemctl restart tbn`.** Verify with `md5sum`
  on the server against local `Get-FileHash` before restarting. Steering doc
  `.kiro/steering/server-info.md` has the key path and IP.
- **Local Flask boot needs Postgres on 5433** which isn't running; governance
  logging fails but is non-blocking. For local tests set
  `TBN_MEMORY_REQUIRE_NETWORK_GOVERNANCE=0` and call `memory_service` directly
  rather than booting the whole app.
- **`data/test_memory_tiers.py` and siblings target `/opt/tbn-protocol`** (a Linux
  prod path) and won't run locally as-is.

---

## 7. OPEN THREADS

Carried from 19 Aug, still open:
- CV Harvard AI course dates still a placeholder ("2025–2026" vs "Dec 2025–Jun
  2026" from earlier notes). Regenerate via `data/generate_cv_pdf.py`, don't hand-edit the PDF.
- Whether to add OpenAI credential IDs (776804524 / OPN-PTFG) to the CV.
- HN post `data/hackernews-post-multiplayer.md` drafted, not submitted.
- GSC sitemap tab showed a cosmetic "Temporary processing error"; check the
  property dropdown is domain-level before assuming a real crawl issue.

New from this session:
- **Decide whether to start the scoped EH pilot** and on which tenant.
- **Design a replacement for the Recall@5 gate** — needs an achievable maximum
  (e.g. Recall@k with k scaled to label count, or precision-oriented). This is a
  design decision, not typing.
- **Consider a production abstention signal.** `route()` returns
  `no_candidates` / `candidates_found` but doesn't distinguish genuine relevance
  from incidental word overlap. Design it; don't copy the 0.75 threshold that just
  failed in the harness.
- **Possible G15 ↔ EH wiring** as trusted-source provider (see section 4).
- Any future held-out study needs fresh corpus *and* fresh controls, and separate
  authorization. The Stage Sixteen attempt is spent.
