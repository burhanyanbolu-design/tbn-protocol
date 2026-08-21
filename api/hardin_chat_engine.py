"""
Hardin Chat — engine
=====================
"The same model, but nothing reaches you unverified."

Calls an underlying LLM (OpenAI GPT), runs the raw answer through the
existing Hardin Filter governance checks (G8-G16, hardin_filter_checks.py),
and issues a signed, chained Hardin Filter receipt for the turn before
returning it. Also recalls and stores per-conversation memory so the chat
remembers context across turns, using the same signed memory engine
(tbn_memory.py) as the rest of Hardin Memory.

No new governance logic here -- reuses run_all_checks() / issue_filter_receipt()
already proven in flight-hunter and the heathrowblackcabs-agent. This module
is the server-side counterpart of the CLI prototype at
demos/hardin-chat/hardin_chat.py; behaviour is the same, only the memory
store is now tenant-scoped instead of a single local file, so each customer's
conversations are isolated.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""
import os
import re
import requests

from .hardin_filter_checks import run_all_checks
from .hardin_filter_receipt import issue_filter_receipt, verify_filter_receipt
from . import tbn_memory as mem

CHAT_MEMORY_ROOT = "data/hardin_chat_memory"

# Failure states an answer's checks can land in -- flagged to the caller so
# the UI can show "verified" vs "flagged" without re-deriving the logic.
_BAD_RESULT_TOKENS = ("fabricated", "leak", "overconfident_unsourced", "contradicts",
                     "unable_to_verify", "inconsistent", "stale")


def _safe_id(value: str, default: str = "default") -> str:
    safe = "".join(c for c in (value or "") if c.isalnum() or c in "_-")
    return safe or default


def _tenant_chat_db(tenant_id: str) -> str:
    os.makedirs(CHAT_MEMORY_ROOT, exist_ok=True)
    return os.path.join(CHAT_MEMORY_ROOT, _safe_id(tenant_id) + ".sqlite")


def call_openai(question: str, model: str = None) -> str:
    """Minimal call to OpenAI's chat completion API. Returns the raw answer text."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured on this server")
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": question}],
            "temperature": 0.7,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def recall_context(tenant_id: str, conversation_id: str, query: str, k: int = 5) -> list:
    """Pull back signed memories for this conversation. Every returned item is
    a verified, unaltered shard -- recall() rejects anything whose signature
    doesn't check out, so nothing tampered gets fed back into the prompt."""
    db_path = _tenant_chat_db(tenant_id)
    out = mem.recall(query, k=k, db_path=db_path,
                     principal={"agent_id": "hardin-chat", "store_scope": f"hardin-chat:{tenant_id}"},
                     private=True, require_governance=False)
    results = out.get("results") or []
    prefix = f"hardin-chat:{conversation_id}"
    return [r for r in results if r.get("source", "").startswith(prefix)]


def remember_turn(tenant_id: str, conversation_id: str, question: str, answer: str) -> dict:
    """Store this turn as a signed, chained memory shard so a later turn in
    the same conversation can recall it -- and so what was remembered can be
    proven, not just trusted."""
    db_path = _tenant_chat_db(tenant_id)
    text = f"User asked: {question}\nAssistant answered: {answer}"
    return mem.remember(text, kind="conversation_turn",
                        source=f"hardin-chat:{conversation_id}",
                        db_path=db_path, auto_version=True,
                        principal={"agent_id": "hardin-chat", "store_scope": f"hardin-chat:{tenant_id}"},
                        private=True, require_governance=False)


def hardin_chat_turn(tenant_id: str, conversation_id: str, question: str,
                     model: str = None, trusted_sources: list = None) -> dict:
    """
    The full governed turn: recall past context, ask the model, check the
    answer, sign a receipt, remember this turn for next time.

    Returns a dict with question, recalled_context, answer, source_ai,
    checks, flags, receipt, receipt_verified, memory_shard_id, memory_signed.
    """
    conversation_id = _safe_id(conversation_id)
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    recalled = recall_context(tenant_id, conversation_id, question)

    prompt = question
    if recalled:
        context_block = "\n".join(f"- {r['text']}" for r in recalled)
        prompt = (
            "Here is verified prior context from this conversation "
            "(each item is a signed, tamper-checked memory):\n"
            f"{context_block}\n\n"
            f"Now answer this question, using that context where relevant:\n{question}"
        )

    answer = call_openai(prompt, model=model)

    checks = run_all_checks(
        question, answer,
        live_check=True,
        trusted_sources=trusted_sources,
        enable_escalation=False,
    )

    flags = []
    for c in checks:
        result = (c.get("result") or "").lower()
        if any(token in result for token in _BAD_RESULT_TOKENS):
            flags.append({"layer": c["layer"], "name": c["name"],
                         "result": c["result"], "detail": c.get("detail", "")})

    receipt = issue_filter_receipt(question, answer, checks, source=f"openai:{model}")
    verification = verify_filter_receipt(receipt)

    remembered = remember_turn(tenant_id, conversation_id, question, answer)

    return {
        "question": question,
        "recalled_context": [{"shard_id": r.get("shard_id"), "text": r.get("text")} for r in recalled],
        "answer": answer,
        "source_ai": f"openai:{model}",
        "checks": checks,
        "flags": flags,
        "verified": len(flags) == 0,
        "receipt": receipt,
        "receipt_id": receipt.get("receipt_id"),
        "receipt_chain_index": receipt.get("chain_index"),
        "receipt_verified": verification.get("valid", False),
        "memory_shard_id": remembered.get("shard_id"),
        "memory_signed": remembered.get("signed", remembered.get("deduplicated", False)),
        "memory_deduplicated": remembered.get("deduplicated", False),
        "conversation_id": conversation_id,
    }
