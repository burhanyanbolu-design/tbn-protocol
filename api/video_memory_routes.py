"""
Video Memory API routes — to be added to server.py
These endpoints let you query what the video agent has learned.
"""


# ── Add these routes to server.py ─────────────────────────────────────

# Route 1: Query the agent's memory
@app.route("/api/video-agent/ask", methods=["POST"])
def video_agent_ask():
    """
    Ask the video agent a question about what it has learned.
    Uses Gemini to synthesise an answer from all stored memories.
    
    Body: {"question": "Who is Burhan Yanbolu?"}
    """
    import json as json_mod
    import google.generativeai as genai
    from api.video_memory import query_memory, get_memory_stats

    GEMINI_KEY = "AIzaSyAmM_DYDI1riSrHuOaQJNu-6ZKDze40of8"
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    data = request.get_json(force=True) if request.is_json else {}
    question = data.get("question", request.form.get("question", "")).strip()

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Search memory
    results = query_memory(question)

    # Build context from memories
    context_parts = []

    if results["people_found"]:
        for person in results["people_found"]:
            context_parts.append(f"PERSON: {person['name']}")
            context_parts.append(f"  Mentioned {person['mentions']} times across {len(person['sources'])} videos")
            for fact in person.get("facts", [])[:20]:
                context_parts.append(f"  - {fact}")

    if results["memories_found"]:
        for mem in results["memories_found"][:5]:
            context_parts.append(f"\nVIDEO SOURCE: {mem.get('source', 'unknown')}")
            context_parts.append(f"  Summary: {mem.get('summary', '')}")
            if mem.get("transcript"):
                context_parts.append(f"  What was said: {mem.get('transcript', '')}")

    if not context_parts:
        return jsonify({
            "answer": "I haven't learned anything about that yet. Feed me more videos and I'll build up my knowledge.",
            "sources": 0,
            "stats": get_memory_stats(),
        })

    # Use Gemini to synthesise a natural answer
    prompt = f"""You are the TBN Video Agent. You have watched multiple videos and built up knowledge.
A user is asking you a question. Answer ONLY from the knowledge below — do not make things up.
If the knowledge is incomplete, say what you know and what you're not sure about.

QUESTION: {question}

YOUR KNOWLEDGE (from videos you've watched):
{chr(10).join(context_parts)}

Give a clear, confident answer based on what you've learned from watching these videos."""

    try:
        response = model.generate_content(prompt)
        answer = response.text.strip()
    except Exception as e:
        # Fallback: return raw facts
        answer = f"Based on {len(results['memories_found'])} videos I've watched:\n"
        for person in results["people_found"]:
            answer += f"\n{person['name']}:\n"
            for fact in person.get("facts", [])[:10]:
                answer += f"  • {fact}\n"

    return jsonify({
        "answer": answer,
        "question": question,
        "sources_used": len(results["memories_found"]),
        "people_referenced": [p["name"] for p in results["people_found"]],
        "stats": get_memory_stats(),
    })


# Route 2: Get memory stats
@app.route("/api/video-agent/memory", methods=["GET"])
def video_agent_memory():
    """Return what the video agent knows — stats, people, topics."""
    from api.video_memory import get_memory_stats
    return jsonify(get_memory_stats())


# Route 3: Get everything known about a person
@app.route("/api/video-agent/person/<name>", methods=["GET"])
def video_agent_person(name):
    """Get everything the agent knows about a specific person."""
    from api.video_memory import _load_json, PEOPLE_FILE
    people = _load_json(PEOPLE_FILE)

    # Search by key or name
    name_lower = name.lower().replace(" ", "_")
    person = people.get(name_lower)

    if not person:
        # Try partial match
        for key, p in people.items():
            if name_lower in key or name_lower in p["name"].lower():
                person = p
                break

    if not person:
        return jsonify({"error": f"No knowledge about '{name}' yet. Feed me videos about them."}), 404

    return jsonify(person)
