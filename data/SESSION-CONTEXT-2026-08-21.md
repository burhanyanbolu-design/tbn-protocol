# SESSION CONTEXT — 21 August 2026

Continues from `data/SESSION-CONTEXT-2026-08-20.md`. This session: TBN 0.1.6
PyPI fix + publish, LinkedIn outreach (Sneha/Kriscent, Vishakha follow-up,
Sherry Turkle/James/Pinar/Simon replies), Server 2 diagnosis (false alarm),
and building/testing Hardin Chat — a governed chat prototype now with a real
web UI, but with one real unresolved limitation found and documented, not
fixed. **Do not present Hardin Chat as customer-ready — the memory-recall
limitation below must be resolved or the claim scoped down first.**

All commits pushed. `tbn-protocol` `origin/main` at `566ae24`.

---

## 1. TBN PROTOCOL 0.1.6 — SHIPPED TO PYPI, LIVE

Sneha Jain (AI Consultant, Kriscent Techno Hub) asked for docs/demo on TBN.
While answering, found the published SDK's own quickstart was broken:
`client.register()` called `/api/register`, which is now admin-locked
(`"Bot registration is not available publicly"`). Anyone following the
README hit a wall immediately.

**Fixed and published `tbn-protocol` 0.1.6** (was 0.1.5):
- `register()` now calls the real self-service endpoint
  (`/api/access/request` — instant trial key, 7 days, 100 calls/day)
- New: `verify_public()`, `verify_record()` (zero-trust GAR verification),
  `get_chain()`, `get_public_key()`, `plans()` — all no-key-needed
- Built and published from the Lightsail server (no local `.pypirc`/twine on
  this machine) — Burhan generated a scoped PyPI API token, used once for
  `twine upload`, then revoked it after (confirmed done).
- Verified live end-to-end against `tbn.hardinai.co.uk` before and after
  publish: `verify_public`, `get_public_key` (RSA-PSS-SHA256, 2048-bit),
  `verify_record` against a real GAR, `get_chain`, `plans` all respond
  correctly with zero API key.
- Source at `api/pypi-package/` in this repo (not committed to git — it's a
  separate publish artifact, matches what's live on PyPI now).

**Deliverables sent to Sneha:** a one-page developer leaflet
(`data/leaflet-tbn-protocol-developer.md`) explaining the 9-layer GAR,
verify flow, and quickstart, honest about what TBN does/doesn't prove. Also
turned into a single-page visual leaflet (image, not saved as a file this
session — recreate via the Canva/image-gen prompt already given if needed
again). Confirmed AGPL-3.0 + the leaflet make zero partner/Shango claims —
safe per the "no joint claims without mutual sign-off" term.

**LinkedIn activity this session (check whether all were actually posted):**
- TBN 0.1.6 announcement post drafted (hashtags, PyPI link, GAR explainer)
- Reply to Simon Erskine Locke (Tauth Labs/C2PA) re: SB 942 three-phase law
- Reply to Vishakha Gupta (aperture-nexus) follow-up nudge after her
  "will take a few days" pause
- Replies to Sherry Turkle (ChatGPT flattery/hallucination post — led to the
  Hardin Chat idea, see below), James W. Niu (ambient-agent restraint
  question), Pinar Patton (SIDAL loop) — all under the same Shaun Johnson
  repost thread

---

## 2. SERVER 2 / HARDINAI LABS — FALSE ALARM, CONFIRMED HEALTHY

Dashboard showed "discovery cron hasn't run in 1218 minutes — Needs
attention." Investigated both servers:

- **Server 1** (3.11.229.68, the brain — TBN/Memory/dashboard): its LOCAL
  `hardinai_labs_discover.log` hasn't been touched since 19 July (discovery
  moved to Server 2 back then). The dashboard health check reads this dead
  local file instead of the synced one.
- **Server 2** (13.43.181.12, key `$env:TEMP\s2key.pem`, separate AWS
  account "squerd enterprises"): genuinely healthy. Cron running hourly
  (`hardinai_labs_discover.py`) and every 30 min
  (`content_authenticity_discover.py`), confirmed real runs at 22:00, 23:00,
  00:00 ingesting 10-15 sources each. Daily sync to Server 1 at 04:15 UTC
  confirmed running (`labs_sync_to_s1.sh`), last successful sync yesterday.

**Not fixed, not urgent:** the dashboard's staleness check needs to read
`data/hardinai_labs_ingest_log/log.jsonl` (the synced file, fresh) instead
of `data/hardinai_labs_discover.log` (dead local file, permanently stale).
Cosmetic — the actual pipeline is fine, only the warning is wrong.

---

## 3. HARDIN CHAT — BUILT, TESTED, ONE REAL BUG FOUND UNDER RIGOR

Sherry Turkle's LinkedIn post (ChatGPT insisted a fabricated citation
existed, then flattered her for catching it) prompted: "could we build our
own GPT wrapper with our governance on top?" Answer worked through
carefully:

**Naming:** "HardinGPT" rejected — OpenAI trademarks "GPT" and enforces it.
Settled on **Hardin Chat** (`chat.hardinai.co.uk` unclaimed, no
trademark risk, matches existing Hardin/TBN product naming).

**What it actually is, scoped correctly:** NOT stopping ChatGPT from
fabricating (impossible — no third party can reach inside a closed model).
IS catching fabrication *before the user trusts it* — call the model,
check the output, sign a receipt. Positioned honestly in every draft as
"the same model, but nothing reaches you unverified," never "we fixed
ChatGPT."

**What it deliberately does NOT use, and why (both correct decisions):**
- **NOT Tier-1 signed facts** (`tbn_memory_tiers.record_fact`) — its own
  docstring requires `privileged=True` and explicitly refuses
  user-asserted/model-inferred content. Chat memory is exactly what Tier-1
  exists to reject. Using it would contradict the security guarantee.
- **NOT HMRU** — a hardware R&D concept (dedicated memory chip prototype,
  tested on real Arduino UNO Q hardware with power-loss tests). Nothing to
  do with conversation memory. Corrected Burhan's assumption before
  building anything.
- **NOT Area Five / the shadow router** — has two open bugs from the 20
  Aug session (abstention threshold, Recall@5 gate) and is explicitly a
  narrowing/routing layer, not a chat-memory primitive. Kept scope
  deliberately separate so Hardin Chat's own issues don't get tangled with
  Area Five's.

**What it DOES use:** the general governed memory engine
(`api/tbn_memory.py` `remember()`/`recall()`), the same one
`memory_service.py` wraps for real Hardin Memory customers — correct choice,
signed/chained, designed for exactly this.

### Build 1 — CLI prototype (`demos/hardin-chat/hardin_chat.py`), committed `ea87bfe`

Calls OpenAI GPT-4o-mini → runs answer through existing
`hardin_filter_checks.run_all_checks()` (G8-G16, unmodified, already proven
in flight-hunter/heathrowblackcabs-agent) → signs receipt via
`hardin_filter_receipt.issue_filter_receipt()` → recalls/stores per-turn
memory via `tbn_memory.remember()/recall()`.

**Real tests, no mocking:** 4 initial governance tests including one genuine
catch — asked about a nonexistent PyPI package (`turbo-json-fastparse-9000`),
GPT-4o-mini confidently gave install instructions, **G10 correctly flagged
"2 fabricated of 2 references checked"** (live-checked PyPI), **G9 flagged
overconfident_unsourced**. Receipt signed, independently re-verified.

Also ran 2-turn "memory" tests (Marcus/marine-biologist, Priya/teal) that
appeared to work at the time — **this appearance turned out to be
misleading, see the bug below.**

**Security fix during this build:** `_gen_test_key.py` (throwaway local test
signing key, explicitly NOT the production key) had generated a private key
file that was untracked AND ungitignored — one `git add -A` from landing in
the public repo. Deleted the key material, added `api/.gitignore` with
`*.pem` coverage. Confirmed `api/.env` (real API keys) has zero git history.

### Build 2 — Web UI (`api/hardin_chat_engine.py`, `hardin_chat_routes.py`,
`templates/hardin_chat.html`), committed `566ae24`

Server-side version: same governed-turn logic, now behind real Flask
routes using the EXISTING tenant/API-key auth (`Bearer`/`X-API-Key`, same
system as `/v1/memory/*`). Memory is now tenant-scoped — one sqlite file per
`tenant_id` under `data/hardin_chat_memory/`, not a single shared file.

- `POST /v1/chat/message` — one governed turn, requires API key
- `POST /v1/chat/verify` — zero-trust receipt verification, no key needed
- `GET /chat` — the UI page

UI matches existing dark/cyan/monospace Hardin visual language (same
palette as `memory_demo_bot.html`, `multiplayer.html`). Shows
verified/flagged badges per turn, a recalled-context badge, and a clickable
detail panel with the actual G8-G16 results and receipt fields.

**Verified via Flask `test_client` with real GPT calls:** page loads (200,
10852 bytes), unauthenticated POST correctly 401s, authenticated turn
returns verified answer + re-verified receipt, standalone `/v1/chat/verify`
correctly confirms a receipt object.

### THE REAL BUG — found under rigorous re-testing, NOT fixed, flagged for next time

While re-verifying multi-turn recall through the Flask path, "What's my
hobby?" failed to recall a stored fact about astronomy that it should have
found. Traced to the root cause in `api/tbn_memory.py`'s `recall()`:

```python
if private and _keyword_score(query, row["text"]) <= 0.0:
    continue
```

**In private mode (the default — `_normalise_principal` hardcodes
`"private": True` unless explicitly set `False`), recall requires at least
one literal shared word (>2 chars) between the query and the stored text.
There is no semantic/paraphrase matching in this mode.** Confirmed with an
engineered zero-overlap test: stored "Zara enjoys stargazing every clear
night with her telescope," queried "What is my favourite hobby?" —
`_keyword_score` returns exactly `0.0`, recall returns exactly `0` results.
Reproduced consistently across multiple isolated test runs.

**This contradicts the earlier "it works" claims from earlier in the same
session.** Re-examined: those earlier successful transcripts (Marcus/marine
biologist, "What's my job?") almost certainly had incidental keyword overlap
that went unnoticed — not genuine paraphrase understanding. Did not chase
down the exact prior transcript further; the current, controlled,
reproducible test is what matters, and it fails.

**Three options for next session, not yet decided:**
1. Ship with the limitation documented — "recall works when the follow-up
   reuses a word from what was said" is still real value, just narrower
   than assumed.
2. Enrich the recall query — extract key entities/nouns from conversation
   history, include them alongside the natural-language question when
   calling `mem.recall()`, to make overlap more likely without touching the
   underlying engine.
3. Investigate whether a non-private embedding path (`_local_embed` is
   used either way per `_embed()`'s logic when `private=True` — need to
   check if there's a genuinely different, non-keyword-gated path at all,
   or if this constraint is fundamental to the local/offline embedding
   design) would give real semantic matching. Changes what "private" means
   for this data — needs a real decision, not a quick swap.

**Do not claim "Hardin Chat remembers conversations" without resolving this
or scoping the claim down to "recalls things when you use similar words."**

---

## 4. STANDING NOTES / GOTCHAS THIS SESSION

- **`grep_search` intermittently returned empty results for
  `api/tbn_memory.py` specifically** even for strings confirmed present via
  direct `Select-String` / `read_file`. Cause unclear (large file, some
  indexing staleness). If grep comes back suspiciously empty on a file you
  know has the content, fall back to `Select-String` (PowerShell) or
  `read_file` with a line range before concluding the code doesn't exist.
- **Server 2 access:** `13.43.181.12`, key `$env:TEMP\s2key.pem` (also
  `C:\Users\Burhan Yanbolu\Downloads\LightsailDefaultKey-eu-west-2 (6).pem`),
  user `ubuntu`. Separate AWS account from Server 1 ("squerd enterprises")
  — no shared console access.
- **`api/tbn_memory.py` and most of `api/` are untracked in git** — SCP'd to
  production over many sessions but never committed. No git history to diff
  against when behavior seems to have changed between sessions; can't rule
  out the file itself changed on disk without a snapshot. Worth remembering
  if "this used to work" comes up again.
- **PyPI publish requires `twine`/`build` + a token — none present
  locally or on Server 1 by default.** Had to `pip install build twine` on
  the server, hit a `setuptools>=68.0` mismatch (server has 59.6, Ubuntu
  22.04 system package) and a `pyproject.toml`-not-read-by-old-setuptools
  issue — worked around with a `setup.cfg` fallback. If publishing again,
  expect the same two issues.
- **PowerShell truncation/garbling of long piped output continues** — same
  issue as prior sessions. Redirect to a file and `Get-Content` it rather
  than piping directly through `Select-Object -Last N` when output is long
  or contains non-ASCII (mojibake shows up but doesn't indicate a real
  problem — always double check against the actual file/DB content before
  trusting garbled console text).

---

## 5. OPEN THREADS

Carried from 19-20 Aug, still open:
- CV Harvard AI course dates placeholder, OpenAI credential IDs decision.
- HN post (`data/hackernews-post-multiplayer.md`) still not submitted.
- Area Five: abstention threshold fix + Recall@5 gate redesign — both
  deliberately NOT touched this session (correctly kept separate from
  Hardin Chat work).
- Scoped EH pilot (`AREA_FIVE_SHADOW_TENANTS`) — built, not yet started on
  a real tenant.

New from this session, in priority order for next time:
- **Decide and implement the memory-recall fix** (see section 3) before
  showing Hardin Chat to anyone as "remembers your conversation."
- Wider Hardin Chat testing — only ~10 real conversations total across both
  builds. Needs volume (different topics, longer threads, adversarial
  prompts) before quoting a real catch rate.
- Cost-per-conversation measurement — not yet done. Needed before any
  pricing decision.
- If/when ready: deploy `hardin_chat_engine.py` + `hardin_chat_routes.py` +
  `hardin_chat.html` to the Lightsail server and register the blueprint in
  the real `server.py` (pattern: `health_agent.py`'s
  `/memory/demo/support-bot` route is the template to follow).
- Dashboard staleness-check fix for Hardin Labs (cosmetic, low priority —
  read the synced log path, not the dead local one).
- Commercialisation shape discussed but not started: compliance/audit-trail
  positioning (not "better chatbot"), per-seat or per-verified-conversation
  pricing above GPT pass-through cost, private beta with 1-2 existing
  pipeline contacts (Sneha, or a governance-adjacent LinkedIn contact)
  before any public opening.
