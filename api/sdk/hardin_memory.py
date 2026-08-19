"""
Hardin Memory — official Python client (zero dependencies)
==========================================================

Drop this single file into your project and you have hardened, poison-proof,
verifiable memory for your AI agent in a few lines. Standard library only.

    from hardin_memory import HardinMemory

    mem = HardinMemory("YOUR_API_KEY")
    mem.remember("Customer prefers email over phone.", kind="fact", source="crm")

    hits = mem.recall("how does the customer like to be contacted?")
    for h in hits["results"]:
        print(h["score"], h["text"], "verified:", h["verified"])

    proof = mem.audit()          # {"verdict": "INTACT", ...}

    # Facts update honestly instead of being overwritten or rejected:
    mem.remember("Customer now prefers phone over email.",
                 kind="fact", source="crm", auto_version=True)
    # → old preference is superseded (signed), never deleted
    timeline = mem.history(shard_id)   # every version, verified, in order

Every call is hardened and verified automatically — lies can't get in, and you
can prove the memory is clean. Get a key at https://memory.hardinai.co.uk

© 2026 Hardin Enterprises Ltd. Provided for use with the Hardin Memory service.
"""

import json
import urllib.request
import urllib.error
import urllib.parse

DEFAULT_BASE = "https://memory.hardinai.co.uk"


class HardinMemoryError(Exception):
    """Raised when the API returns an error or is unreachable."""


class HardinMemory:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE, timeout: int = 30):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def _call(self, method: str, path: str, body: dict = None) -> dict:
        url = self.base + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", "Bearer " + self.api_key)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            raise HardinMemoryError(f"HTTP {e.code}: {detail}") from None
        except urllib.error.URLError as e:
            raise HardinMemoryError(f"connection error: {e.reason}") from None

    def remember(self, text: str, kind: str = "fact", source: str = "api",
                auto_version: bool = False, supersedes: str = None) -> dict:
        """Store a memory. Returns {shard_id, signed, chain_index, created,
        versioned, supersedes}.

        auto_version=True: if this contradicts an existing verified memory, it
        is stored as a new SIGNED fact that supersedes the old one (a temporal
        edge) instead of being rejected. The old fact is never deleted — only
        marked historical. supersedes=<shard_id>: explicitly version a named
        fact you already know is being replaced."""
        return self._call("POST", "/v1/memory/remember",
                          {"text": text, "kind": kind, "source": source,
                           "auto_version": auto_version, "supersedes": supersedes})

    def recall(self, query: str, k: int = 5) -> dict:
        """Find the most relevant VERIFIED, CURRENT memories. Poisoned/forged
        ones, and superseded (outdated) versions of a fact, are never returned.
        Returns {query, results:[{text, score, verified, supersedes, ...}]}."""
        return self._call("POST", "/v1/memory/recall", {"query": query, "k": k})

    def verify(self, shard_id: str) -> dict:
        """Check one memory's seal. Returns {found, valid, ...}."""
        return self._call("GET", "/v1/memory/verify/" + shard_id)

    def history(self, shard_id: str) -> dict:
        """Full signed version timeline for one fact — every prior belief, when
        it changed, and independent proof none of it was tampered with.
        Returns {version_count, timeline: [{text, is_current, verified, ...}]}."""
        return self._call("GET", "/v1/memory/history/" + shard_id)

    def entities(self, type: str = None) -> dict:
        """Every named entity (email/company) this store has linked, ranked by
        mentions. Returns {entities: [{name, type, mentions, ...}], count}."""
        return self._call("GET", self._q("/v1/memory/entities", {"type": type}))

    def entity_history(self, name: str) -> dict:
        """Direct fact history for one named entity — current + superseded
        shards, no semantic guessing required."""
        return self._call("GET", "/v1/memory/entities/" + urllib.parse.quote(name, safe=""))

    def audit(self) -> dict:
        """Prove the whole memory is clean. Returns {verdict, current_shards,
        superseded_shards, ...}."""
        return self._call("GET", "/v1/memory/audit")

    def usage(self) -> dict:
        """Your current usage and plan."""
        return self._call("GET", "/v1/memory/usage")

    # ── 3-tier trust split ────────────────────────────────────────────
    # Tier 1 = facts of record (immutable, signed) — the ONLY entitlement source.
    # Tier 2 = preferences (mutable, low-trust) — can never grant a right.
    # Tier 3 = learned policy (gated) — propose, then a human approves.
    def _q(self, path: str, params: dict) -> str:
        clean = {k: v for k, v in params.items() if v is not None}
        return path + ("?" + urllib.parse.urlencode(clean) if clean else "")

    # Tier 1 — facts of record
    def record_fact(self, fact_type: str, subject: str, data: dict, source: str) -> dict:
        """Append a SIGNED fact of record (refund issued, entitlement granted, …).
        `source` must name the verified system event, e.g. 'stripe:invoice.paid'.
        This is the only thing entitlement decisions trust. Cannot come from user text."""
        return self._call("POST", "/v1/memory/facts", {
            "fact_type": fact_type, "subject": subject, "data": data, "source": source})

    def get_facts(self, fact_type: str = None, subject: str = None) -> dict:
        """Read signed facts by reference (never semantic guessing)."""
        return self._call("GET", self._q("/v1/memory/facts",
                          {"fact_type": fact_type, "subject": subject}))

    def check_entitlement(self, subject: str, entitlement: str) -> dict:
        """Decision-grade check. Reads ONLY Tier-1 signed facts; fails closed.
        Returns {granted: bool, source, ...}."""
        return self._call("GET", self._q("/v1/memory/entitlement",
                          {"subject": subject, "entitlement": entitlement}))

    def revoke_entitlement(self, subject: str, entitlement: str, source: str, reason: str = "") -> dict:
        """Officially cancel an entitlement by appending a signed superseding fact.
        `source` must name the verified system event (e.g. 'stripe:refund.created')."""
        return self._call("POST", "/v1/memory/facts/revoke",
                          {"subject": subject, "entitlement": entitlement,
                           "source": source, "reason": reason})

    def verify_decision(self, receipt: dict) -> dict:
        """Independently verify a signed decision receipt against the public key.
        No API key needed — anyone can verify a decision your agent made."""
        return self._call("POST", "/v1/memory/decision/verify", {"receipt": receipt})

    def facts_audit(self) -> dict:
        """Whole-store integrity proof over the facts of record."""
        return self._call("GET", "/v1/memory/facts/audit")

    # Tier 2 — preferences
    def set_preference(self, key: str, value, source: str = "user") -> dict:
        """Store a soft preference (tone, language, UI). Entitlement-shaped keys
        are refused — Tier-2 can never grant a right."""
        return self._call("PUT", "/v1/memory/preferences",
                          {"key": key, "value": value, "source": source})

    def get_preferences(self) -> dict:
        return self._call("GET", "/v1/memory/preferences")

    # Tier 3 — learned policy (gated)
    def propose_policy(self, name: str, rule: dict, rationale: str = "",
                       proposed_by: str = "learning") -> dict:
        """Propose a learned policy. It stays INERT until approved."""
        return self._call("POST", "/v1/memory/policy/propose",
                          {"name": name, "rule": rule, "rationale": rationale,
                           "proposed_by": proposed_by})

    def pending_policies(self) -> dict:
        return self._call("GET", "/v1/memory/policy/pending")

    def approve_policy(self, proposal_id: str, approver: str, rendered_context: dict = None) -> dict:
        """Activate a proposal (human/governance step). Signs it on approval.

        Pass `rendered_context` = the exact state shown to the approver at
        the moment of approval (session/turn history, other participants'
        actions, etc). It's hashed into `approval_context_hash` on the
        record, so a dispute can distinguish "who approved" from "what they
        actually had in front of them" — informed authority, not just authority."""
        return self._call("POST", "/v1/memory/policy/approve",
                          {"proposal_id": proposal_id, "approver": approver,
                           "rendered_context": rendered_context})

    def reject_policy(self, proposal_id: str, approver: str, reason: str = "",
                      rendered_context: dict = None) -> dict:
        return self._call("POST", "/v1/memory/policy/reject",
                          {"proposal_id": proposal_id, "approver": approver, "reason": reason,
                           "rendered_context": rendered_context})

    def active_policies(self) -> dict:
        return self._call("GET", "/v1/memory/policy")

    def decide(self, subject: str, entitlement: str) -> dict:
        """The safe decision: YES/NO from Tier-1 facts only, personalised by
        Tier-2 prefs, handled per Tier-3 policy. Returns
        {granted, decision_source, personalisation, active_policies}."""
        return self._call("GET", self._q("/v1/memory/decide",
                          {"subject": subject, "entitlement": entitlement}))

    # ── Refusal log (the pressure-valve problem) ───────────────────────
    # A hard refusal that dead-ends gets routed around off-session. Log every
    # refusal, then log what actually happened next — override, escalation,
    # retry, or nothing — so the audit trail isn't silent exactly where the
    # consequential decisions happen.
    def log_refusal(self, action: str, reason: str, subject: str = None,
                    rendered_context: dict = None, source: str = "governance") -> dict:
        """Durably record a refusal. Returns {refusal_id, ...} — keep the
        refusal_id to call record_followup() once you know what happened next."""
        return self._call("POST", "/v1/memory/refusals",
                          {"action": action, "reason": reason, "subject": subject,
                           "rendered_context": rendered_context, "source": source})

    def record_followup(self, refusal_id: str, followup: str, followup_source: str = "system") -> dict:
        """Append what happened after a refusal. Append-only — the original
        refusal record can never be overwritten, only joined with an outcome."""
        return self._call("POST", "/v1/memory/refusals/followup",
                          {"refusal_id": refusal_id, "followup": followup,
                           "followup_source": followup_source})

    def get_refusals(self, subject: str = None) -> dict:
        """All signed refusals joined with their followup (if any). A refusal
        with followup_pending=True has been logged but not yet resolved."""
        return self._call("GET", self._q("/v1/memory/refusals", {"subject": subject}))

    # ── Feedback & learning (Tier 2/3, safe by construction) ───────────
    def record_outcome(self, subject: str, decision: str, outcome: str,
                       sentiment: str = None, signal: dict = None,
                       weight: float = 1.0, context: dict = None) -> dict:
        """Log an outcome (resolved / disputed / escalated / …) for an interaction.
        signal={"pref": {...}} carries preference hints the learner may adopt;
        context={"topic": ...} feeds policy mining. Low-trust — never a decision input."""
        return self._call("POST", "/v1/memory/feedback",
                          {"subject": subject, "decision": decision, "outcome": outcome,
                           "sentiment": sentiment, "signal": signal, "weight": weight,
                           "context": context})

    def feedback_stats(self) -> dict:
        return self._call("GET", "/v1/memory/feedback/stats")

    def learn(self, min_support: int = 3, consistency: float = 0.6) -> dict:
        """Run the learner: adopt consistent preferences (Tier 2) and PROPOSE
        policies (Tier 3, gated). Never grants a right. Returns the report."""
        return self._call("POST", "/v1/memory/learn",
                          {"min_support": min_support, "consistency": consistency})

    def profile(self, subject: str) -> dict:
        """Learned per-subject preference profile (safe to personalise with)."""
        return self._call("GET", self._q("/v1/memory/profile", {"subject": subject}))


if __name__ == "__main__":
    import os, sys
    key = os.environ.get("HARDIN_MEMORY_KEY") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not key:
        print("usage: HARDIN_MEMORY_KEY=... python hardin_memory.py")
        raise SystemExit(1)
    m = HardinMemory(key)
    print("remember:", m.remember("Hello from the Hardin Memory client."))
    print("recall:", m.recall("hello"))
    print("audit:", m.audit())
