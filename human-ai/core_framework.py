"""
Human AI — Culturally Aware, Ethically Grounded AI Learning Framework
=====================================================================
A standalone system for teaching AI philosophical wisdom from books,
with ethical filtering, cultural awareness, and diversity respect.

This is NOT a search engine. It's a teaching & learning system.
You feed it books → it extracts philosophy → it reasons through that lens.

(c) Hardin AI Solutions
"""

import json
import os
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Any


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================================
# 1. ETHICAL FRAMEWORK
# ============================================================================

class EthicalFramework:
    """Filters all knowledge through ethical principles before acceptance"""

    def __init__(self):
        self.manifest = self._load_manifest()
        self.bias_patterns = self.manifest.get("bias_patterns", [])
        self.harmful_keywords = self.manifest.get("harmful_keywords", [])
        self.ethical_principles = self.manifest.get("ethical_principles", {})

    def _load_manifest(self) -> Dict:
        path = os.path.join(BASE_DIR, "ethical_manifest.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "ethical_principles": {
                "respect_autonomy": "Respect individual choice and consent",
                "do_no_harm": "Avoid causing harm to individuals or groups",
                "fairness": "Treat all people equitably regardless of background",
                "transparency": "Be clear about limitations and reasoning",
                "accountability": "Take responsibility for outputs"
            },
            "bias_patterns": [
                "stereotyping", "overgeneralization",
                "exclusionary_language", "power_imbalance",
                "cultural_insensitivity"
            ],
            "harmful_keywords": [
                "discriminate", "dehumanize", "exploit"
            ]
        }

    def evaluate(self, text: str, source: str = "unknown") -> Dict:
        """Evaluate text against ethical framework. Returns score and recommendation."""
        score = 1.0
        flags = []

        text_lower = text.lower()
        for keyword in self.harmful_keywords:
            if keyword in text_lower:
                flags.append(f"Harmful keyword: {keyword}")
                score -= 0.3

        for pattern in self.bias_patterns:
            if self._detect_bias(text, pattern):
                flags.append(f"Potential bias: {pattern}")
                score -= 0.15

        if score < 0.5:
            recommendation = "REJECT"
        elif score < 0.7:
            recommendation = "FLAG_FOR_REVIEW"
        else:
            recommendation = "ACCEPT"

        return {
            "score": round(score, 2),
            "flags": flags,
            "recommendation": recommendation,
            "source": source,
        }

    def _detect_bias(self, text: str, pattern: str) -> bool:
        indicators = {
            "stereotyping": r"\ball\s+\w+\s+(are|always|never)",
            "exclusionary_language": r"(only|truly|real)\s+\w+\s+(can|are|do)",
            "power_imbalance": r"(superior|inferior|civilized|primitive)",
        }
        if pattern in indicators:
            return bool(re.search(indicators[pattern], text.lower()))
        return False


# ============================================================================
# 2. CULTURAL AWARENESS
# ============================================================================

class CulturalAwareness:
    """Detects cultural cues and adapts communication style"""

    def __init__(self):
        self.cultural_data = self._load_data()

    def _load_data(self) -> Dict:
        path = os.path.join(BASE_DIR, "cultural_data.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"dimensions": {}, "respect_norms": {}}

    def infer_context(self, text: str) -> Dict:
        """Infer cultural context from text"""
        context = {
            "communication_preference": "neutral",
            "cultural_cues": [],
            "adaptation_notes": [],
        }

        if any(w in text.lower() for w in ["sir", "madam", "respect", "honor"]):
            context["communication_preference"] = "formal"
            context["adaptation_notes"].append("Use formal language")

        if any(w in text.lower() for w in ["we", "our community", "our family"]):
            context["cultural_cues"].append("collectivist orientation")
            context["adaptation_notes"].append("Frame in group/community context")

        if any(w in text.lower() for w in ["urgent", "immediately", "deadline"]):
            context["adaptation_notes"].append("Time-sensitive communication")

        return context


# ============================================================================
# 3. DIVERSITY AWARENESS
# ============================================================================

class DiversityAwareness:
    """Respects gender identity, pronouns, and human diversity"""

    def extract_preferences(self, text: str) -> Dict:
        """Extract communication preferences from text"""
        preferences = {
            "pronouns": None,
            "style": "neutral",
            "diversity_cues": [],
        }

        # Pronoun detection
        match = re.search(r"(he/him|she/her|they/them)", text.lower())
        if match:
            preferences["pronouns"] = match.group(1)

        # Identity signals
        for keyword in ["neurodivergent", "disabled", "immigrant", "lgbtq"]:
            if keyword in text.lower():
                preferences["diversity_cues"].append(keyword)

        return preferences


# ============================================================================
# 4. KNOWLEDGE BASE (Persistent, Validated)
# ============================================================================

class KnowledgeBase:
    """Stores learned knowledge with ethical filtering and validation"""

    def __init__(self):
        self.db_path = os.path.join(BASE_DIR, "knowledge_base.json")
        self.store = self._load()
        self.ethics = EthicalFramework()

    def _load(self) -> Dict:
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "domains": {},
            "metadata": {"created": datetime.now().isoformat(), "version": "1.0"}
        }

    def save(self):
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.store, f, indent=2, ensure_ascii=False)

    def add(self, domain: str, knowledge: Dict, source: str) -> Dict:
        """Add knowledge after ethical check"""
        text = json.dumps(knowledge)
        check = self.ethics.evaluate(text, source)

        if check["recommendation"] == "REJECT":
            return {"status": "rejected", "reason": check["flags"]}

        entry_id = hashlib.md5((source + text).encode()).hexdigest()[:12]
        entry = {
            "knowledge": knowledge,
            "source": source,
            "added": datetime.now().isoformat(),
            "ethical_score": check["score"],
            "validated": check["score"] >= 0.9,
            "entry_id": entry_id,
        }

        if domain not in self.store["domains"]:
            self.store["domains"][domain] = []
        self.store["domains"][domain].append(entry)
        self.save()

        return {"status": "success", "entry_id": entry_id, "ethical_score": check["score"]}

    def validate(self, entry_id: str):
        """Manually validate a knowledge entry"""
        for domain in self.store["domains"]:
            for entry in self.store["domains"][domain]:
                if entry["entry_id"] == entry_id:
                    entry["validated"] = True
                    entry["validated_at"] = datetime.now().isoformat()
                    self.save()
                    return True
        return False

    def query(self, text: str = None, domain: str = None) -> List[Dict]:
        """Query knowledge — searches across all fields with word matching"""
        results = []
        if not text:
            # Return all validated entries
            for dom, entries in self.store["domains"].items():
                if domain and dom != domain:
                    continue
                for entry in entries:
                    if entry["validated"]:
                        results.append(entry)
            return results

        # Split query into words for flexible matching
        query_words = [w.lower() for w in text.split() if len(w) > 2]

        for dom, entries in self.store["domains"].items():
            if domain and dom.lower() != domain.lower():
                continue
            for entry in entries:
                if not entry["validated"]:
                    continue
                # Search in all knowledge fields + domain + source
                search_text = (
                    json.dumps(entry["knowledge"]).lower() + " " +
                    dom.lower() + " " +
                    entry.get("source", "").lower()
                )
                # Count how many query words match
                matches = sum(1 for w in query_words if w in search_text)
                if matches > 0:
                    entry["_relevance"] = matches / len(query_words)
                    results.append(entry)

        # Sort by relevance
        results.sort(key=lambda x: x.get("_relevance", 0), reverse=True)
        return results

    def stats(self) -> Dict:
        total = sum(len(e) for e in self.store["domains"].values())
        validated = sum(
            1 for entries in self.store["domains"].values()
            for e in entries if e["validated"]
        )
        return {
            "total": total,
            "validated": validated,
            "domains": list(self.store["domains"].keys()),
        }


# ============================================================================
# 5. BOOK IMPORT & PHILOSOPHY EXTRACTION
# ============================================================================

class BookImporter:
    """Import books and extract philosophical knowledge"""

    def __init__(self):
        self.knowledge_base = KnowledgeBase()

    def import_book(self, file_path: str, domain: str) -> Dict:
        """Import a book file and add its knowledge"""
        from pathlib import Path
        path = Path(file_path)

        if not path.exists():
            return {"status": "error", "reason": f"File not found: {file_path}"}

        # Parse based on format
        suffix = path.suffix.lower()
        if suffix == '.pdf':
            content = self._parse_pdf(file_path)
        elif suffix == '.txt':
            content = self._parse_txt(file_path)
        elif suffix == '.epub':
            content = self._parse_epub(file_path)
        elif suffix in ('.html', '.htm'):
            content = self._parse_html(file_path)
        else:
            return {"status": "error", "reason": f"Unsupported format: {path.suffix}. Supported: PDF, TXT, EPUB, HTML"}

        # Chunk and extract
        chunks = self._chunk(content["text"])
        topics = self._extract_topics(chunks)

        # Store as knowledge
        knowledge = {
            "title": content["title"],
            "author": content.get("author", "Unknown"),
            "summary": content["text"][:1000],
            "topics": topics,
            "chunks": len(chunks),
            "pages": content.get("pages", 1),
        }

        result = self.knowledge_base.add(domain, knowledge, f"Book: {content['title']}")
        result["title"] = content["title"]
        result["chunks"] = len(chunks)
        result["topics"] = topics
        return result

    def _parse_pdf(self, path: str) -> Dict:
        import fitz
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        title = doc.metadata.get("title", os.path.basename(path).replace(".pdf", ""))
        author = doc.metadata.get("author", "Unknown")
        pages = len(doc)
        doc.close()
        return {"title": title, "author": author, "text": text, "pages": pages}

    def _parse_txt(self, path: str) -> Dict:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        return {"title": os.path.basename(path).replace(".txt", ""), "text": text, "pages": 1}

    def _parse_epub(self, path: str) -> Dict:
        import zipfile
        text = ""
        with zipfile.ZipFile(path, 'r') as z:
            for name in sorted(z.namelist()):
                if name.endswith(('.html', '.xhtml')):
                    try:
                        content = z.read(name).decode('utf-8')
                        clean = re.sub('<[^<]+?>', '', content)
                        clean = re.sub(r'\s+', ' ', clean).strip()
                        text += clean + "\n"
                    except:
                        pass
        return {"title": os.path.basename(path).replace(".epub", ""), "text": text, "pages": 1}

    def _parse_html(self, path: str) -> Dict:
        """Extract text from HTML file"""
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        # Strip HTML tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        title = ""
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        if not title:
            title = os.path.basename(path).replace(".html", "").replace(".htm", "")
        return {"title": title, "text": text, "pages": 1}

    def _chunk(self, text: str, size: int = 500) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current = ""
        for s in sentences:
            if len(current) + len(s) < size:
                current += " " + s
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = s
        if current.strip():
            chunks.append(current.strip())
        return chunks

    def _extract_topics(self, chunks: List[str]) -> List[str]:
        topics = set()
        for chunk in chunks[:20]:
            found = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', chunk)
            topics.update(found[:3])
        return list(topics)[:15]


# ============================================================================
# 6. HUMAN AI SYSTEM (Main Entry Point)
# ============================================================================

class HumanAI:
    """
    The Human AI system.
    Teaches AI from books with ethical filtering and cultural awareness.
    """

    def __init__(self):
        self.ethics = EthicalFramework()
        self.culture = CulturalAwareness()
        self.diversity = DiversityAwareness()
        self.knowledge = KnowledgeBase()
        self.importer = BookImporter()

    def teach_from_book(self, file_path: str, domain: str) -> Dict:
        """Import a book and teach the system"""
        print(f"\n  Importing: {file_path}")
        print(f"  Domain: {domain}")
        result = self.importer.import_book(file_path, domain)
        if result["status"] == "success":
            print(f"  Added: {result.get('title', 'unknown')} ({result.get('chunks', 0)} chunks)")
            print(f"  Topics: {', '.join(result.get('topics', [])[:5])}")
        else:
            print(f"  Failed: {result.get('reason', 'unknown error')}")
        return result

    def teach(self, domain: str, knowledge: Dict, source: str) -> Dict:
        """Teach knowledge directly"""
        return self.knowledge.add(domain, knowledge, source)

    def query(self, text: str, domain: str = None) -> List[Dict]:
        """Query the knowledge base"""
        return self.knowledge.query(text, domain)

    def process(self, prompt: str) -> Dict:
        """Process a prompt through the full pipeline — uses Ollama to think"""
        ethical = self.ethics.evaluate(prompt)
        if ethical["recommendation"] == "REJECT":
            return {"response": "Cannot process — ethical concern.", "flags": ethical["flags"],
                    "ethical_score": ethical["score"], "knowledge_used": 0}

        cultural = self.culture.infer_context(prompt)
        diversity = self.diversity.extract_preferences(prompt)
        results = self.knowledge.query(prompt)

        # Build context from knowledge
        context = self._build_context(results)

        # Generate response using Ollama (free, local)
        response = self._generate_response(prompt, context, cultural)

        return {
            "response": response,
            "ethical_score": ethical["score"],
            "cultural_context": cultural,
            "knowledge_used": len(results),
        }

    def _build_context(self, results: List[Dict]) -> str:
        """Build knowledge context from search results"""
        if not results:
            return ""

        parts = []
        for entry in results[:3]:
            k = entry["knowledge"]
            if isinstance(k, dict):
                summary = k.get("summary", "")
                if summary:
                    parts.append(summary[:1500])
                topics = k.get("topics", [])
                if topics:
                    parts.append(f"Key topics: {', '.join(topics[:10])}")
        return "\n\n".join(parts)

    def _generate_response(self, prompt: str, context: str, cultural: Dict) -> str:
        """Generate response using Ollama (free, local LLM)"""
        try:
            import requests

            # Build system prompt
            system = """You are Human AI — a culturally aware, ethically grounded assistant.
You have internalized knowledge from books and respond with wisdom, not just facts.
You think through questions using the philosophy and knowledge you've absorbed.
Be thoughtful, concise, and speak naturally — like someone who has genuinely read and understood these works.
Do not list sources or say "based on my knowledge". Just respond naturally with wisdom."""

            if cultural["communication_preference"] == "formal":
                system += "\nThe user prefers formal communication. Use respectful, formal language."

            # Build messages
            messages = [{"role": "system", "content": system}]

            if context:
                messages.append({
                    "role": "system",
                    "content": f"Knowledge you have absorbed:\n\n{context[:3000]}"
                })

            messages.append({"role": "user", "content": prompt})

            # Try Ollama
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={"model": "llama3.2", "messages": messages, "stream": False},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]

        except Exception as e:
            # Fallback if Ollama not running
            return self._fallback_response(prompt, context)

    def _fallback_response(self, prompt: str, context: str) -> str:
        """Fallback when Ollama is not available"""
        if not context:
            return "I don't have specific knowledge on this yet. Teach me by importing a book. (Note: Start Ollama for full AI responses)"

        # Return a summary of what we know
        return f"Based on what I've learned:\n\n{context[:500]}\n\n(Start Ollama for deeper, conversational responses)"

    def status(self) -> Dict:
        stats = self.knowledge.stats()
        return {
            "system": "Human AI",
            "knowledge": stats,
            "ethics": "ACTIVE",
            "cultural_awareness": "ACTIVE",
            "diversity": "ACTIVE",
        }

    def print_status(self):
        s = self.status()
        print("\n" + "=" * 50)
        print("  HUMAN AI — STATUS")
        print("=" * 50)
        print(f"  Knowledge: {s['knowledge']['total']} entries ({s['knowledge']['validated']} validated)")
        print(f"  Domains:   {', '.join(s['knowledge']['domains']) or 'None yet'}")
        print(f"  Ethics:    {s['ethics']}")
        print(f"  Cultural:  {s['cultural_awareness']}")
        print(f"  Diversity: {s['diversity']}")
        print("=" * 50 + "\n")


# ============================================================================
# 7. INTERACTIVE CLI
# ============================================================================

def main():
    """Interactive CLI for Human AI"""
    ai = HumanAI()

    print("\n" + "=" * 50)
    print("  HUMAN AI — Teaching & Learning System")
    print("=" * 50)
    print("\n  Commands: teach, import, query, voice, status, help, exit\n")

    while True:
        try:
            cmd = input("HumanAI > ").strip()
            if not cmd:
                continue

            if cmd == "exit":
                print("\n  Goodbye.\n")
                break
            elif cmd == "help":
                print("""
  COMMANDS:
  ────────────────────────────────────────────
  import           Import a book (PDF/TXT/EPUB)
  teach            Teach knowledge manually
  query <text>     Search the knowledge base
  ask <prompt>     Process a prompt
  status           Show system status

  VOICE (free & offline):
  ────────────────────────────────────────────
  voice            Start voice conversation
  speak <text>     Make AI speak text aloud
  voice-settings   Configure voice (rate, volume)

  UTILITY:
  ────────────────────────────────────────────
  help             Show this help
  exit             Exit
  ────────────────────────────────────────────
""")
            elif cmd == "status":
                ai.print_status()
            elif cmd == "voice":
                try:
                    from speech_module import VoiceAssistant
                    print("\n  Initializing voice assistant...")
                    assistant = VoiceAssistant(ai)
                    assistant.start_conversation()
                except ImportError as e:
                    print(f"  Missing: {e}")
                    print("  Install: pip install pyttsx3 pyaudio vosk")
            elif cmd.startswith("speak "):
                text = cmd[6:]
                try:
                    from speech_module import TextToSpeechEngine
                    tts = TextToSpeechEngine()
                    tts.speak(text)
                except ImportError as e:
                    print(f"  Missing: {e}")
                    print("  Install: pip install pyttsx3")
            elif cmd == "voice-settings":
                try:
                    from speech_module import TextToSpeechEngine
                    tts = TextToSpeechEngine()
                    print("\n  Available Voices:")
                    tts.list_voices()
                    rate = input("  Speaking rate (50-300, default 150): ").strip() or "150"
                    volume = input("  Volume (0.0-1.0, default 0.9): ").strip() or "0.9"
                    tts.set_rate(int(rate))
                    tts.set_volume(float(volume))
                    tts.speak("Voice settings updated.")
                    print("  Done.")
                except Exception as e:
                    print(f"  Error: {e}")
            elif cmd == "import":
                path = input("  File path: ").strip()
                domain = input("  Domain (e.g. Philosophy, Psychology): ").strip()
                if path and domain:
                    ai.teach_from_book(path, domain)
            elif cmd == "teach":
                domain = input("  Domain: ").strip()
                concept = input("  Concept: ").strip()
                principle = input("  Principle: ").strip()
                if domain and concept:
                    ai.teach(domain, {"concept": concept, "principle": principle}, "manual")
                    print("  Added.")
            elif cmd.startswith("query "):
                text = cmd[6:]
                results = ai.query(text)
                if results:
                    print(f"\n  Found {len(results)} results:")
                    for r in results[:5]:
                        print(f"    - {r['source']} (score: {r['ethical_score']})")
                else:
                    print("  No results.")
            elif cmd.startswith("ask "):
                prompt = cmd[4:]
                result = ai.process(prompt)
                print(f"\n  {result['response']}")
                print(f"  [ethical: {result['ethical_score']}]\n")
            else:
                # Treat as a prompt
                result = ai.process(cmd)
                print(f"\n  {result['response']}")
                print(f"  [ethical: {result['ethical_score']}]\n")

        except KeyboardInterrupt:
            print("\n\n  Goodbye.\n")
            break
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    main()
