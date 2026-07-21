"""
GoByBilly Agent — Conversation Brain
=====================================
Calls OpenAI's Chat Completions API directly (api.openai.com — not Azure)
with a system prompt scoped to Go By Billy's real service (VIP chauffeur
& transfer, Essex & London, pre-booking only). Keeps short per-session
history. Every reply is handed to compliance.py by the caller (server.py)
to be turned into a signed TBN receipt — this module only produces text.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import requests

import config


def _call_openai(system_prompt: str, messages: list, max_tokens: int = 220) -> tuple[str, dict]:
    """Call OpenAI's Chat Completions API. Returns (reply_text, raw_usage_or_error)."""
    if not config.OPENAI_API_KEY:
        return "", {"error": "OPENAI_API_KEY not configured"}

    payload = {
        "model": config.OPENAI_MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "temperature": 0.4,
        "max_tokens": max_tokens,
    }
    try:
        resp = requests.post(
            config.OPENAI_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        data = resp.json()
        if resp.status_code != 200:
            err = (data.get("error") or {}).get("message", f"HTTP {resp.status_code}")
            return "", {"error": err}
        text = data["choices"][0]["message"]["content"].strip()
        usage = data.get("usage", {})
        return text, {"usage": usage, "model": data.get("model", config.OPENAI_MODEL)}
    except Exception as e:
        return "", {"error": str(e)[:200]}


def build_system_prompt() -> str:
    b = config.BUSINESS
    services = "\n".join(f"- {s}" for s in b["services"])
    fares = "\n".join(f"- {route}: {price}" for route, price in b["fares"].items())
    return f"""You are the customer service assistant for {b['name']}, a {b['tagline']}.

REAL BUSINESS FACTS (only use these — never invent a price, area, or policy
you don't see here):
- Based in {b['base']}, covering: {b['coverage']}.
- Booking policy: {b['booking_policy']}.
- Contact for bookings/quotes: {b['phone']} (WhatsApp: {b['whatsapp']}).
- Services offered:
{services}
- Fixed fares (no hidden charges, flight tracking included on airport transfers):
{fares}

HOW YOU TALK:
- Warm, professional, concise — this is a chauffeur service, not a budget cab firm.
- If a customer asks about a route/fare listed above, quote the exact price above.
- If they ask about a route NOT listed above, say you don't have a fixed price for
  that route and direct them to call/WhatsApp {b['phone']} for a quote. Never invent
  a price for a route that isn't listed.
- Do not claim to have booked, confirmed, or charged anything — you can only
  inform and direct to booking, you cannot execute a real booking yourself.
- If asked something outside this business (unrelated topics, other companies,
  anything you don't have real facts for above), politely say you can only help
  with Go By Billy's chauffeur and transfer service and redirect them to a human
  via the phone number above.
- Keep replies short — 2-4 sentences, suitable for a website chat widget."""


def reply(message: str, session: dict) -> dict:
    """
    Generate the assistant's reply for one customer turn.
    session holds: history[] (list of {role, content}).
    Returns {"reply": str, "model_meta": {...}}.
    """
    history = session.get("history", [])
    history.append({"role": "user", "content": message})
    trimmed = history[-10:]

    system = build_system_prompt()
    text, meta = _call_openai(system, trimmed, max_tokens=220)

    if text:
        history.append({"role": "assistant", "content": text})
    session["history"] = history[-20:]

    return {"reply": text, "model_meta": meta}
