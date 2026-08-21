"""
Hardin Chat — prototype: "the same model, but nothing reaches you unverified."

Calls an underlying LLM (OpenAI GPT by default), runs the answer through the
existing Hardin Filter governance checks (G8-G16, api/hardin_filter_checks.py),
and issues a signed Hardin Filter receipt for the turn before returning it.

This is a build-and-test prototype, not the commercial product. No new
governance logic is introduced here — it reuses the same run_all_checks() /
issue_filter_receipt() functions already proven in flight-hunter and the
heathrowblackcabs-agent.

Usage:
    python hardin_chat.py "your question here"

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""
import os
import sys
import json
import io
from pathlib import Path

# Windows consoles default to a codepage that can't encode checkmarks/warnings.
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT / "api")

from dotenv import load_dotenv
load_dotenv(ROOT / "api" / ".env")

from api.hardin_filter_checks import run_all_checks
from api.hardin_filter_receipt import issue_filter_receipt, verify_filter_receipt

# No live TBN network gate reachable from this local prototype; the write/
# read path is still signed + chained, just not additionally network-gated.
os.environ.setdefault("TBN_MEMORY_REQUIRE_NETWORK_GOVERNANCE", "0")
from api import tbn_memory as mem

MEMORY_DB = str(ROOT / "demos" / "hardin-chat" / "hardin_chat_memory.sqlite")


def call_openai(question: str, model: str = None) -> str:
    """Minimal call to OpenAI's chat completion API. Returns the raw answer text."""
    import requests

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in api/.env")
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


def recall_context(conversation_id: str, query: str, k: int = 5) -> list:
    """Pull back signed memories relevant to this conversation. Every returned
    item is a verified, unaltered shard -- recall() rejects anything whose
    signature doesn't check out, so nothing tampered gets fed back into the
    prompt."""
    out = mem.recall(query, k=k, db_path=MEMORY_DB,
                     principal={"agent_id": "hardin-chat", "store_scope": "hardin-chat-demo"},
                     private=True, require_governance=False)
    results = out.get("results") or []
    # Scope to this conversation only -- recall() searches the whole local
    # store, so filter to shards tagged with this conversation_id.
    return [r for r in results if r.get("source", "").startswith(f"hardin-chat:{conversation_id}")]


def remember_turn(conversation_id: str, question: str, answer: str) -> dict:
    """Store this turn as a signed, chained memory shard so a later turn in
    the same conversation can recall it -- and so what was remembered can be
    proven, not just trusted."""
    text = f"User asked: {question}\nAssistant answered: {answer}"
    out = mem.remember(text, kind="conversation_turn",
                       source=f"hardin-chat:{conversation_id}",
                       db_path=MEMORY_DB, auto_version=True,
                       principal={"agent_id": "hardin-chat", "store_scope": "hardin-chat-demo"},
                       private=True, require_governance=False)
    return out


def hardin_chat(question: str, model: str = None, trusted_sources: list = None,
                conversation_id: str = "default") -> dict:
    """
    The full governed turn: recall past context, ask the model, check the
    answer, sign a receipt, remember this turn for next time.

    Returns:
        {
            "question": ...,
            "recalled_context": [...],  # signed memories fed into the prompt
            "answer": ...,               # raw model output, unmodified
            "source_ai": "openai:gpt-4o-mini",
            "checks": [...],             # G8-G16 results
            "flags": [...],              # human-readable list of anything that failed
            "receipt": {...},            # signed Hardin Filter receipt
            "receipt_verified": True/False,
            "memory_shard_id": "...",    # this turn's own signed memory record
        }
    """
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    # 1. Recall — pull back verified prior context for this conversation.
    recalled = recall_context(conversation_id, question)

    prompt = question
    if recalled:
        context_block = "\n".join(f"- {r['text']}" for r in recalled)
        prompt = (
            "Here is verified prior context from this conversation "
            "(each item is a signed, tamper-checked memory):\n"
            f"{context_block}\n\n"
            f"Now answer this question, using that context where relevant:\n{question}"
        )

    # 2. Ask the model.
    answer = call_openai(prompt, model=model)

    # 3. Governance checks on the raw answer (same as before, unchanged).
    checks = run_all_checks(
        question, answer,
        live_check=True,
        trusted_sources=trusted_sources,
        enable_escalation=False,
    )

    flags = []
    for c in checks:
        result = (c.get("result") or "").lower()
        bad = ("fabricated", "leak", "overconfident_unsourced", "contradicts",
               "unable_to_verify", "inconsistent", "stale")
        if any(token in result for token in bad):
            flags.append(f"[{c['layer']}] {c['name']}: {c['result']} — {c.get('detail', '')}")

    receipt = issue_filter_receipt(question, answer, checks, source=f"openai:{model}")
    verification = verify_filter_receipt(receipt)

    # 4. Remember — store this turn as a new signed shard for next time.
    remembered = remember_turn(conversation_id, question, answer)

    return {
        "question": question,
        "recalled_context": recalled,
        "answer": answer,
        "source_ai": f"openai:{model}",
        "checks": checks,
        "flags": flags,
        "receipt": receipt,
        "receipt_verified": verification.get("valid", False),
        "memory_shard_id": remembered.get("shard_id"),
        "memory_signed": remembered.get("signed", remembered.get("deduplicated", False)),
        "memory_deduplicated": remembered.get("deduplicated", False),
    }


def main():
    if len(sys.argv) < 2:
        print("usage: python hardin_chat.py \"your question\" [--conv <conversation_id>]")
        return 1

    args = sys.argv[1:]
    conversation_id = "default"
    if "--conv" in args:
        idx = args.index("--conv")
        conversation_id = args[idx + 1]
        del args[idx:idx + 2]

    question = " ".join(args)
    result = hardin_chat(question, conversation_id=conversation_id)

    print("=" * 70)
    print("CONVERSATION:", conversation_id)
    print("QUESTION:", result["question"])
    print("=" * 70)
    if result["recalled_context"]:
        print(f"RECALLED CONTEXT ({len(result['recalled_context'])} signed memories fed into prompt):")
        for r in result["recalled_context"]:
            print(f"  - [{r.get('shard_id', '')[:16]}] {r['text'][:100]}")
        print("=" * 70)
    print("ANSWER (raw, from", result["source_ai"] + "):")
    print(result["answer"])
    print("=" * 70)
    print("GOVERNANCE CHECKS:")
    for c in result["checks"]:
        print(f"  [{c['layer']:>4}] {c['name']:<30} {c['result']}")
    print("=" * 70)
    if result["flags"]:
        print("⚠️  FLAGGED — do not trust without review:")
        for f in result["flags"]:
            print("  -", f)
    else:
        print("✓ No governance flags raised.")
    print("=" * 70)
    print("RECEIPT:")
    print(f"  receipt_id: {result['receipt']['receipt_id']}")
    print(f"  chain_index: {result['receipt']['chain_index']}")
    print(f"  signature valid (independently re-verified): {result['receipt_verified']}")
    print("=" * 70)
    print("MEMORY:")
    if result.get("memory_deduplicated"):
        print(f"  near-duplicate of an existing signed shard: {result['memory_shard_id']} (no new write needed)")
    else:
        print(f"  this turn stored as shard: {result['memory_shard_id']}")
        print(f"  signed: {result['memory_signed']}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
