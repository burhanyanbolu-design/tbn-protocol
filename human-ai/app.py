"""
Human AI — Web Dashboard
=========================
Combines:
  - Philosophy bot chat (teach from books, chat with wisdom)
  - Knowledge management (import, validate, query)
  - Ethical framework status
  - Cultural awareness

Run: python app.py
URL: http://localhost:5015
"""

import os
import sys
import json
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core_framework import HumanAI, EthicalFramework, KnowledgeBase

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
ai = HumanAI()

# Philosophy bot storage
BOTS_DIR = os.path.join(BASE_DIR, "bots")
os.makedirs(BOTS_DIR, exist_ok=True)
BOOKS_DIR = os.path.join(BASE_DIR, "books")
os.makedirs(BOOKS_DIR, exist_ok=True)


def load_bots() -> list:
    """Load all philosophy bots"""
    bots = []
    registry_path = os.path.join(BOTS_DIR, "registry.json")
    if os.path.exists(registry_path):
        with open(registry_path, 'r') as f:
            data = json.load(f)
            bots = data.get("bots", [])
    return bots


def save_bots(bots: list):
    """Save bots registry"""
    registry_path = os.path.join(BOTS_DIR, "registry.json")
    with open(registry_path, 'w') as f:
        json.dump({"bots": bots}, f, indent=2)


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/status')
def api_status():
    return jsonify(ai.status())


@app.route('/api/bots')
def api_bots():
    bots = load_bots()
    return jsonify({"bots": bots})


@app.route('/api/knowledge')
def api_knowledge():
    stats = ai.knowledge.stats()
    entries = []
    for domain, items in ai.knowledge.store["domains"].items():
        for item in items:
            entries.append({
                "domain": domain,
                "source": item["source"],
                "validated": item["validated"],
                "ethical_score": item["ethical_score"],
                "added": item["added"],
                "entry_id": item["entry_id"],
            })
    return jsonify({"stats": stats, "entries": entries})


@app.route('/api/teach', methods=['POST'])
def api_teach():
    data = request.get_json(force=True) or {}
    domain = data.get("domain", "")
    concept = data.get("concept", "")
    principle = data.get("principle", "")
    source = data.get("source", "manual")

    if not domain or not concept:
        return jsonify({"error": "Domain and concept required"})

    result = ai.teach(domain, {"concept": concept, "principle": principle}, source)
    return jsonify(result)


@app.route('/api/import_book', methods=['POST'])
def api_import_book():
    """Import a book via file upload"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files['file']
    domain = request.form.get('domain', 'Philosophy')
    bot_name = request.form.get('bot_name', '')
    book_title = request.form.get('book_title', '')
    author = request.form.get('author', 'Unknown')

    if not file.filename:
        return jsonify({"error": "No file selected"})

    # Save file
    filename = file.filename
    filepath = os.path.join(BOOKS_DIR, filename)
    file.save(filepath)

    # Import into knowledge base
    result = ai.teach_from_book(filepath, domain)

    # If bot_name provided, create a philosophy bot
    if bot_name and result.get("status") == "success":
        bot_id = f"human-ai-{secrets.token_hex(6)}"
        bot_entry = {
            "bot_id": bot_id,
            "bot_name": bot_name,
            "book_title": book_title or result.get("title", filename),
            "author": author,
            "domain": domain,
            "created": datetime.now().isoformat(),
            "knowledge_entry_id": result.get("entry_id"),
            "topics": result.get("topics", []),
        }
        bots = load_bots()
        bots.append(bot_entry)
        save_bots(bots)
        result["bot_created"] = bot_entry

    return jsonify(result)


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat with the Human AI system"""
    data = request.get_json(force=True) or {}
    message = data.get("message", "")
    bot_id = data.get("bot_id")

    if not message:
        return jsonify({"error": "No message"})

    # Process through the AI pipeline
    result = ai.process(message)

    # If a specific bot is selected, add its context
    if bot_id:
        bots = load_bots()
        bot = next((b for b in bots if b["bot_id"] == bot_id), None)
        if bot:
            result["bot_name"] = bot["bot_name"]
            result["book_context"] = bot["book_title"]

    return jsonify(result)


@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    """Evaluate text through ethical framework"""
    data = request.get_json(force=True) or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"})
    result = ai.ethics.evaluate(text)
    return jsonify(result)


@app.route('/api/speak', methods=['POST'])
def api_speak():
    """Generate speech audio using edge-tts (Sonia neural voice)"""
    import asyncio
    import edge_tts
    from flask import send_file as send_audio

    data = request.get_json(force=True) or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "No text"})

    # Limit text length
    text = text[:5000]

    # Generate audio
    audio_dir = os.path.join(BASE_DIR, ".audio_cache")
    os.makedirs(audio_dir, exist_ok=True)
    audio_path = os.path.join(audio_dir, "response.mp3")

    try:
        async def generate():
            communicate = edge_tts.Communicate(text, "en-GB-SoniaNeural", rate="+0%")
            await communicate.save(audio_path)

        asyncio.run(generate())
        return send_audio(audio_path, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "human-ai"})


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n  Human AI — Dashboard")
    print("  http://localhost:5015")
    print("  Press Ctrl+C to stop\n")
    app.run(host='0.0.0.0', port=5015, debug=False)
