"""
Answer Verification Layer
=========================
Sits between "AI writes an answer" and "user sees it". A normal LLM always
produces *an* answer, so it invents one when it doesn't know. This layer runs
an INDEPENDENT verification pass that:

  1. breaks the answer into individual factual claims
  2. judges each claim SUPPORTED / UNSUPPORTED against the sources used
  3. computes a grounding score (supported / total)
  4. rewrites the answer: keeps supported claims, flags unsupported ones as
     "[unverified]" — or abstains entirely if too little is supported

The point is not a perfect answer. It's an HONEST one: the agent never
confidently states what it cannot support, and tells you when it doesn't know.

verify_answer(...) never raises — on any failure it returns a pass-through
result so the agent still responds.

THREE STATES, AND THE DEFAULT IS THE HONEST ONE (added 12 Aug 2026)
------------------------------------------------------------------
Because this function FAILS OPEN, a reply that was never checked used to be
indistinguishable from one that passed: callers only had `verified` (bool)
and a rewritten answer, so an unrun verifier and a clean pass produced the
same downstream record. That is silence converting itself into a settled
fact with nothing recording the conversion.

Every result therefore now carries an explicit `state`:

    "grounded"          the check RAN and the answer is adequately supported
    "failed_grounding"  the check RAN and the answer is NOT supported (abstain)
    "not_checked"       the check DID NOT RUN (no key, transport error,
                        malformed verifier output, timeout)

An unchecked answer is not "probably fine" — it is UNCHECKED, and presenting
it at the confidence of a checked one is the error. "Sourced" and "verified"
are different questions and must not blur.

Every field that existed before is unchanged, so existing callers keep
working; `state` is additive. Callers SHOULD surface or record it rather
than treating a pass-through as a pass. `api/calibrated_claims.py` now
persists a signed record even for "not_checked", so the absence of a check
is itself on the record.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0
"""

import os
import json
import requests as _req


def _passthrough(answer, reason=""):
    # state="not_checked" is the whole point of the pass-through: the answer is
    # returned untouched, and the caller is told plainly that NOTHING verified
    # it — rather than inferring "fine" from the absence of a complaint.
    return {"verified": False, "grounding_score": None, "verdict": "UNVERIFIED",
            "verified_answer": answer, "claims": [], "abstain": False,
            "unsupported_count": 0, "note": reason, "state": "not_checked"}


def verify_answer(question, answer, sources, *, min_score=50):
    """Independently verify an answer's claims against the sources it used.

    Args:
      question: what the user asked
      answer:   the draft answer the agent produced
      sources:  list of {uri,title} (or []) that grounded the answer
      min_score: below this grounding score, the agent abstains

    Returns a dict with verified/grounding_score/verdict/verified_answer/
    claims/abstain/unsupported_count. Never raises.
    """
    answer = (answer or "").strip()
    if not answer:
        return _passthrough(answer, "empty answer")

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    if not GEMINI_API_KEY:
        return _passthrough(answer, "verifier unavailable")

    src_lines = "\n".join(
        f"- {(s.get('title') or '').strip()} ({(s.get('uri') or '').strip()})"
        for s in (sources or []) if isinstance(s, dict)
    ) or "(no live sources were retrieved)"

    prompt = f"""You are a STRICT, independent fact-verification layer. You did NOT write the
answer below — your only job is to check it, like a careful editor who assumes
nothing is true until the sources back it up.

QUESTION:
{question}

PROPOSED ANSWER:
{answer}

SOURCES THAT WERE AVAILABLE:
{src_lines}

Break the answer into its distinct factual claims. For each claim decide:
- "SUPPORTED"   — a listed source plausibly backs this specific claim
- "UNSUPPORTED" — no listed source backs it, OR no sources were available, OR it
                  is the kind of specific fact (number, name, date, quote, event)
                  that REQUIRES a source and has none.
Opinions, general reasoning and clearly-common-knowledge statements are "SUPPORTED".

Then write "verified_answer": the same answer but with every UNSUPPORTED factual
claim rewritten to make the uncertainty explicit, e.g. wrap it as
"[unverified: ...]" or replace it with "I could not verify this from the sources."
Keep supported content intact. Do not add new facts.

Return ONLY JSON:
{{
  "claims": [{{"claim": "...", "status": "SUPPORTED|UNSUPPORTED"}}],
  "grounding_score": <0-100 integer = supported / total * 100>,
  "verified_answer": "...",
  "summary": "one short sentence on how well-grounded the answer is"
}}
JSON only."""

    try:
        r = _req.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.0, "maxOutputTokens": 2000,
                                       "responseMimeType": "application/json",
                                       "thinkingConfig": {"thinkingBudget": 0}}},
            timeout=40)
        txt = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "") or "{}"
        data = json.loads(txt)
    except Exception as e:
        return _passthrough(answer, f"verifier error: {str(e)[:80]}")

    claims = data.get("claims") or []
    if not isinstance(claims, list):
        claims = []
    total = len(claims)
    supported = sum(1 for c in claims if isinstance(c, dict) and c.get("status") == "SUPPORTED")
    unsupported = total - supported
    score = data.get("grounding_score")
    if not isinstance(score, (int, float)):
        score = int(round(supported / total * 100)) if total else (0 if not sources else 50)
    score = max(0, min(100, int(score)))

    verified_answer = (data.get("verified_answer") or answer).strip()
    abstain = score < min_score
    if abstain and total:
        verified_answer = ("⚠️ I couldn't verify enough of this from reliable sources to answer confidently.\n\n"
                           + verified_answer)

    verdict = "PASS" if score >= 80 else ("PARTIAL" if score >= min_score else "FAIL")

    return {"verified": True, "grounding_score": score, "verdict": verdict,
            "verified_answer": verified_answer, "claims": claims,
            "abstain": abstain, "unsupported_count": unsupported,
            "supported_count": supported, "total_claims": total,
            "note": data.get("summary", ""),
            # Only a check that actually ran can reach these two states.
            "state": "failed_grounding" if abstain else "grounded"}
