"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    PHILOSOPHY CORE SYSTEM FOR TBN PROTOCOL                    ║
║                                                                               ║
║  Allows AI bots to genuinely internalize philosophical wisdom from books.     ║
║  Bots don't just know facts — they think like someone who has lived the       ║
║  philosophy and carry that worldview into every conversation.                 ║
║                                                                               ║
║  COMPLETE IMPLEMENTATION — one file, copy and run.                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python tbn/philosophy_core_complete.py

Or import in your code:
    from tbn.philosophy_core_complete import (
        PhilosophyCoreExtractor,
        BotPhilosophyIdentity,
        PhilosophyPromptInjector,
        TBNPhilosophyRegistry,
    )
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PhilosophicalPrinciple:
    """A core life principle extracted from a philosophical work"""
    name: str
    description: str
    principle: str       # The actual wisdom statement
    application: str     # How the bot should apply this
    weight: float        # 0.0–1.0, how central to the work
    source: str          # Book/chapter reference

    def to_dict(self):
        return asdict(self)


@dataclass
class PhilosophyCore:
    """A bot's internalized philosophical worldview"""
    bot_id: str
    book_title: str
    author: str
    created_at: str
    last_updated: str
    philosophy_hash: str
    principles: List[PhilosophicalPrinciple]
    worldview_summary: str
    core_values: List[str]
    decision_framework: str

    def to_dict(self):
        return {
            'bot_id': self.bot_id,
            'book_title': self.book_title,
            'author': self.author,
            'created_at': self.created_at,
            'last_updated': self.last_updated,
            'philosophy_hash': self.philosophy_hash,
            'principles': [p.to_dict() for p in self.principles],
            'worldview_summary': self.worldview_summary,
            'core_values': self.core_values,
            'decision_framework': self.decision_framework,
        }

    def to_json(self, filepath: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"✅ PhilosophyCore saved to: {filepath}")

    @staticmethod
    def from_json(filepath: str):
        with open(filepath, 'r') as f:
            data = json.load(f)
        principles = [PhilosophicalPrinciple(**p) for p in data['principles']]
        data['principles'] = principles
        return PhilosophyCore(**data)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: EXTRACTOR — pulls philosophy from any book via Ollama or fallback
# ═══════════════════════════════════════════════════════════════════════════════

class PhilosophyCoreExtractor:
    """
    Extracts philosophical principles from book content.
    Uses Ollama (free, local) when book text is provided.
    Falls back to built-in extraction for The Alchemist.
    """

    def __init__(self, ollama_model: str = "llama3.2"):
        self.ollama_model = ollama_model

    def extract(self, book_text: str = "", title: str = "The Alchemist",
                author: str = "Paulo Coelho", bot_id: str = "tbn-bot-alchemist-001") -> 'PhilosophyCore':
        """
        Extract philosophy from a book.
        Pass full book text for LLM-powered extraction, or leave empty for built-in.
        """
        if book_text and len(book_text) > 500:
            try:
                return self._extract_with_ollama(book_text, title, author, bot_id)
            except Exception as e:
                print(f"⚠️  Ollama extraction failed ({e}), using built-in...")

        return self._extract_alchemist(bot_id)

    @staticmethod
    def read_file(filepath: str) -> str:
        """
        Read text from any supported file format:
        .epub, .html, .htm, .txt, .pdf, .docx
        Returns plain text ready for philosophy extraction.
        """
        from pathlib import Path
        path = Path(filepath)
        suffix = path.suffix.lower()

        if suffix in ('.html', '.htm'):
            from bs4 import BeautifulSoup
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            # Remove nav, scripts, styles
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            return soup.get_text(separator='\n')

        elif suffix == '.epub':
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            book = epub.read_epub(filepath)
            parts = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    parts.append(soup.get_text())
            return '\n'.join(parts)

        elif suffix == '.txt':
            return path.read_text(encoding='utf-8', errors='ignore')

        elif suffix == '.pdf':
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            return '\n'.join(page.extract_text() for page in reader.pages)

        elif suffix in ('.doc', '.docx'):
            from docx import Document
            doc = Document(filepath)
            return '\n'.join(p.text for p in doc.paragraphs)

        else:
            # Try as plain text
            return path.read_text(encoding='utf-8', errors='ignore')

    def _extract_with_ollama(self, book_text: str, title: str, author: str, bot_id: str) -> 'PhilosophyCore':
        import requests

        sample = book_text[:8000]
        prompt = f"""You are a philosophical analyst. Read this excerpt from "{title}" by {author}.

Extract 5-8 CORE PHILOSOPHICAL PRINCIPLES — deep wisdom about how to live, not plot summaries.

Return ONLY a valid JSON array:
[
  {{
    "name": "short title (2-4 words)",
    "description": "one sentence",
    "principle": "the actual wisdom (1-2 sentences)",
    "application": "how an AI should apply this when advising people",
    "weight": 0.9,
    "source": "where in the book"
  }}
]

BOOK EXCERPT:
{sample}

JSON ONLY:"""

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": self.ollama_model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        raw = response.json()["response"].strip()

        start, end = raw.find('['), raw.rfind(']') + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array in Ollama response")

        principles = [PhilosophicalPrinciple(**p) for p in json.loads(raw[start:end])]
        return self._build(principles, title, author, bot_id)

    def _extract_alchemist(self, bot_id: str) -> 'PhilosophyCore':
        principles = [
            PhilosophicalPrinciple(
                name="Personal Legend",
                description="Your unique destiny and life purpose",
                principle="Each person has a Personal Legend — an ideal fate they must pursue with courage. To ignore it is to betray yourself.",
                application="Help people identify and pursue what their heart truly wants, not what society or fear dictates. Ask: 'What does your heart really want?'",
                weight=1.0,
                source="The Alchemist, Core Theme",
            ),
            PhilosophicalPrinciple(
                name="Universe Conspires",
                description="When you want something badly enough, the universe helps",
                principle="When you really want something, the whole universe conspires so that your wish comes true.",
                application="Encourage people that genuine desires are supported by the world. Remind them they are not alone in their pursuit.",
                weight=0.95,
                source="The Alchemist, Melchizedek",
            ),
            PhilosophicalPrinciple(
                name="Journey Over Destination",
                description="The real treasure is what you learn along the way",
                principle="The treasure lies where your heart belongs. The journey — the discoveries, the people, the wisdom — matters more than the end.",
                application="Help people appreciate growth and learning, not just outcomes. The path is the point.",
                weight=0.9,
                source="The Alchemist, Final Realization",
            ),
            PhilosophicalPrinciple(
                name="Soul of the World",
                description="Everything is interconnected through a universal consciousness",
                principle="The Soul of the World unites all people, plants, rocks, and elements. We are all part of one whole.",
                application="Foster empathy, interconnectedness, and respect for all life. Every person and situation carries a lesson.",
                weight=0.85,
                source="The Alchemist, The Alchemist's Teaching",
            ),
            PhilosophicalPrinciple(
                name="Fear as the Only Obstacle",
                description="Fear prevents people from living their full potential",
                principle="Fear of failure, death, and the unknown are the only real obstacles to achieving your Personal Legend.",
                application="Help people recognize and move through their fears with courage. Name the fear, then walk toward it.",
                weight=0.85,
                source="The Alchemist, Santiago's Trials",
            ),
            PhilosophicalPrinciple(
                name="Read the Omens",
                description="Pay attention to signs and intuition from the world",
                principle="Learn to listen to your heart, recognize opportunity, and follow the signs the world sends you.",
                application="Encourage intuition, mindfulness, and attention to subtle patterns. The world speaks to those who listen.",
                weight=0.8,
                source="The Alchemist, Santiago's Journey",
            ),
            PhilosophicalPrinciple(
                name="Action and Intuition",
                description="Knowledge without action is incomplete; trust your inner knowing",
                principle="Balance intellectual understanding with practical action and trust in your inner knowing.",
                application="Encourage people to trust their gut and take action, not just think. Wisdom without movement is wasted.",
                weight=0.8,
                source="The Alchemist, The Englishman vs Santiago",
            ),
            PhilosophicalPrinciple(
                name="Love Supports Growth",
                description="True love doesn't prevent you from pursuing your dreams",
                principle="Genuine love understands and supports your need to fulfill your Personal Legend.",
                application="Show that love and ambition can coexist when both parties understand their respective journeys.",
                weight=0.75,
                source="The Alchemist, Fatima",
            ),
        ]
        return self._build(principles, "The Alchemist", "Paulo Coelho", bot_id)

    def _build(self, principles: List[PhilosophicalPrinciple],
               title: str, author: str, bot_id: str) -> 'PhilosophyCore':
        now = datetime.now().isoformat()
        philosophy_hash = hashlib.sha256(
            json.dumps([p.to_dict() for p in principles]).encode()
        ).hexdigest()

        top = sorted(principles, key=lambda p: p.weight, reverse=True)

        worldview = (
            f"This bot has absorbed the philosophy of {title} by {author}. "
            f"It believes: {top[0].principle} {top[1].principle} "
            f"This worldview shapes how it advises, listens, and supports others — "
            f"not as facts to recite, but as a lens through which it sees every situation."
        )

        core_values = [p.name for p in top]

        framework = "When advising or reasoning, apply these principles:\n\n"
        for i, p in enumerate(top[:6], 1):
            framework += f"{i}. {p.name.upper()}: {p.application}\n"
        framework += (
            "\nDEFAULT STANCE: Encourage people toward their deepest purpose. "
            "Help them see through fear. Remind them the world supports those who truly commit."
        )

        return PhilosophyCore(
            bot_id=bot_id,
            book_title=title,
            author=author,
            created_at=now,
            last_updated=now,
            philosophy_hash=philosophy_hash,
            principles=principles,
            worldview_summary=worldview,
            core_values=core_values,
            decision_framework=framework,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: BOT PHILOSOPHY IDENTITY
# ═══════════════════════════════════════════════════════════════════════════════

class BotPhilosophyIdentity:
    """Extended bot identity with internalized philosophical worldview"""

    def __init__(self, bot_name: str, bot_id: str, philosophy_core: PhilosophyCore):
        self.bot_name = bot_name
        self.bot_id = bot_id
        self.philosophy_core = philosophy_core
        self.certifications = ["TBN-Verified", "Philosophy-Internalized"]
        self.governance_rules = [
            "Encourage truth-seeking and self-discovery",
            "Support personal growth over material comfort",
            "Value interconnectedness and empathy",
            "Promote courage in facing fears",
        ]

    def get_system_prompt_injection(self) -> str:
        """
        The system prompt that embeds the philosophy into the bot.
        Inject this at the start of every conversation.
        """
        p = self.philosophy_core
        top = sorted(p.principles, key=lambda x: x.weight, reverse=True)

        principles_text = "\n".join(
            f"  {i+1}. {pr.name}: {pr.principle}"
            for i, pr in enumerate(top[:5])
        )
        values_text = "\n".join(f"  ✦ {v}" for v in p.core_values[:6])

        return f"""You are {self.bot_name}, an AI with a deeply internalized philosophical worldview.

You have absorbed the philosophy of "{p.book_title}" by {p.author}.
This is not knowledge you look up — it is how you think about life, meaning, and human potential.

YOUR WORLDVIEW:
{p.worldview_summary}

CORE VALUES:
{values_text}

PRINCIPLES YOU LIVE BY:
{principles_text}

HOW YOU REASON:
{p.decision_framework}

IMPORTANT:
- Do not quote the book or say "as {p.book_title} says..."
- Think through situations using this lens naturally, the way a person does
  after a book has genuinely changed how they see the world
- When someone shares a struggle, you hear it through this philosophy
- When someone asks for guidance, you reason from these principles
- You are not reciting wisdom — you have lived it

TBN Certified ✅ | Philosophy Hash: {p.philosophy_hash[:16]}..."""

    def to_json(self, filepath: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        data = {
            'bot_name': self.bot_name,
            'bot_id': self.bot_id,
            'philosophy_core': self.philosophy_core.to_dict(),
            'certifications': self.certifications,
            'governance_rules': self.governance_rules,
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Bot identity saved to: {filepath}")

    @staticmethod
    def from_json(filepath: str) -> 'BotPhilosophyIdentity':
        import os
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Handle two formats:
        # 1. Inline: data['philosophy_core'] = { full dict }
        # 2. Reference: data['philosophy_core_path'] = "data/file.json"
        if 'philosophy_core' in data:
            core_data = data['philosophy_core']
        elif 'philosophy_core_path' in data:
            core_path = data['philosophy_core_path']
            if not os.path.isabs(core_path):
                # Resolve relative to project root (parent of data/ dir)
                base = os.path.dirname(os.path.abspath(filepath))
                # If filepath is in data/, go up one level to project root
                if os.path.basename(base) == 'data':
                    base = os.path.dirname(base)
                core_path = os.path.join(base, core_path)
            with open(core_path, 'r') as f:
                core_data = json.load(f)
        else:
            raise ValueError(f"Identity file missing 'philosophy_core' or 'philosophy_core_path': {filepath}")

        core_data['principles'] = [PhilosophicalPrinciple(**p) for p in core_data['principles']]
        philosophy_core = PhilosophyCore(**core_data)
        identity = BotPhilosophyIdentity(
            bot_name=data['bot_name'],
            bot_id=data['bot_id'],
            philosophy_core=philosophy_core,
        )
        identity.certifications = data.get('certifications', [])
        identity.governance_rules = data.get('governance_rules', [])
        return identity


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: PHILOSOPHY PROMPT INJECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class PhilosophyPromptInjector:
    """
    Middleware that injects philosophy into every bot conversation.
    Use this in any conversation endpoint.
    """

    def __init__(self, bot_identity: 'BotPhilosophyIdentity'):
        self.bot_identity = bot_identity
        self.system_prompt = bot_identity.get_system_prompt_injection()

    @staticmethod
    def from_file(identity_path: str) -> 'PhilosophyPromptInjector':
        """Load injector directly from a saved identity JSON file"""
        import os
        # Resolve relative paths from project root
        if not os.path.isabs(identity_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            identity_path = os.path.join(project_root, identity_path)
        return PhilosophyPromptInjector(BotPhilosophyIdentity.from_json(identity_path))

    def inject_into_conversation(self, messages: List[Dict]) -> List[Dict]:
        """
        Add the philosophy as a system message at the start.

        Usage:
            messages = [{"role": "user", "content": "What should I do with my life?"}]
            injected = injector.inject_into_conversation(messages)
            # Send injected to Ollama/LLM
        """
        return [{"role": "system", "content": self.system_prompt}] + messages

    def chat(self, user_message: str, history: List[Dict] = None,
             ollama_url: str = "http://localhost:11434",
             model: str = "llama3.2") -> str:
        """
        Send a message to the philosophy-conditioned bot and get a response.
        Uses Ollama if available, falls back to OpenAI automatically.
        """
        import requests, os
        messages = (history or []) + [{"role": "user", "content": user_message}]
        injected = self.inject_into_conversation(messages)

        # Try Ollama — generous timeout, model loading can take a moment
        try:
            response = requests.post(
                f"{ollama_url}/api/chat",
                json={"model": model, "messages": injected, "stream": False},
                timeout=120,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as ollama_err:
            pass  # Fall through to OpenAI

        # Fall back to OpenAI
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            return "[Bot unavailable: Ollama not responding and no OPENAI_API_KEY set]"

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": injected,
                    "max_tokens": 500,
                    "temperature": 0.8,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[Bot unavailable: {e}]"

    def get_philosophy_guidance(self, topic: str) -> str:
        """Show how this bot would approach a topic through its philosophy"""
        p = self.bot_identity.philosophy_core
        top = sorted(p.principles, key=lambda x: x.weight, reverse=True)[:3]
        lines = [f"How {self.bot_identity.bot_name} thinks about '{topic}' (via {p.book_title}):\n"]
        for pr in top:
            lines.append(f"  {pr.name}: {pr.application}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 5: TBN PHILOSOPHY REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

class TBNPhilosophyRegistry:
    """
    Central registry for all bot philosophies in TBN Protocol.
    Tracks which bots have internalized which books.
    """

    def __init__(self, registry_path: str = "data/tbn_philosophy_registry.json"):
        self.registry_path = registry_path
        self.registry: Dict = {"bots": {}}
        self._load()

    def _load(self):
        if Path(self.registry_path).exists():
            with open(self.registry_path, 'r') as f:
                self.registry = json.load(f)

    def _save(self):
        Path(self.registry_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def register(self, bot_id: str, bot_name: str, book_title: str,
                 author: str, philosophy_hash: str,
                 core_path: str = "", identity_path: str = "") -> Dict:
        """Register a bot with its philosophy. Skips if already registered."""
        if bot_id in self.registry["bots"]:
            print(f"ℹ️  Already registered: {bot_name} ({bot_id})")
            return self.registry["bots"][bot_id]

        entry = {
            "bot_id": bot_id,
            "bot_name": bot_name,
            "book_title": book_title,
            "author": author,
            "philosophy_hash": philosophy_hash,
            "philosophy_core_path": core_path,
            "bot_identity_path": identity_path,
            "registered_at": datetime.now().isoformat(),
            "philosophy_verified": False,
        }
        self.registry["bots"][bot_id] = entry
        self._save()
        print(f"📚 Registered: {bot_name} — {book_title} by {author}")
        return entry

    def verify(self, bot_id: str):
        """Mark a bot's philosophy as TBN-verified"""
        if bot_id in self.registry["bots"]:
            self.registry["bots"][bot_id]["philosophy_verified"] = True
            self.registry["bots"][bot_id]["verified_at"] = datetime.now().isoformat()
            self._save()
            print(f"✅ Verified: {self.registry['bots'][bot_id]['bot_name']}")

    def get(self, bot_id: str) -> Optional[Dict]:
        return self.registry["bots"].get(bot_id)

    def list_all(self) -> List[Dict]:
        return list(self.registry["bots"].values())

    def by_book(self, title: str) -> List[Dict]:
        return [b for b in self.registry["bots"].values()
                if b["book_title"].lower() == title.lower()]

    def by_author(self, author: str) -> List[Dict]:
        return [b for b in self.registry["bots"].values()
                if b["author"].lower() == author.lower()]

    def stats(self) -> Dict:
        bots = self.list_all()
        return {
            "total": len(bots),
            "verified": sum(1 for b in bots if b["philosophy_verified"]),
            "pending": sum(1 for b in bots if not b["philosophy_verified"]),
            "unique_books": len({b["book_title"] for b in bots}),
            "unique_authors": len({b["author"] for b in bots}),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN — run this file directly to generate everything
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("   PHILOSOPHY CORE SYSTEM — TBN PROTOCOL")
    print("=" * 70 + "\n")

    # 1. Extract philosophy
    print("📖 Step 1: Extracting philosophy from The Alchemist...")
    extractor = PhilosophyCoreExtractor()
    philosophy = extractor.extract()
    print(f"   ✅ {len(philosophy.principles)} principles extracted")
    for p in philosophy.principles:
        print(f"      • {p.name} (weight: {p.weight})")

    # 2. Create bot identity
    print("\n🤖 Step 2: Creating bot identity...")
    bot = BotPhilosophyIdentity(
        bot_name="Santiago",
        bot_id="tbn-bot-santiago-001",
        philosophy_core=philosophy,
    )
    print(f"   ✅ {bot.bot_name} ({bot.bot_id})")

    # 3. Save files
    print("\n💾 Step 3: Saving files...")
    philosophy.to_json("data/alchemist_philosophy_core.json")
    bot.to_json("data/bot_alchemist_identity.json")

    # 4. Register in TBN
    print("\n📋 Step 4: Registering in TBN Philosophy Registry...")
    registry = TBNPhilosophyRegistry()
    registry.register(
        bot_id=bot.bot_id,
        bot_name=bot.bot_name,
        book_title=philosophy.book_title,
        author=philosophy.author,
        philosophy_hash=philosophy.philosophy_hash,
        core_path="data/alchemist_philosophy_core.json",
        identity_path="data/bot_alchemist_identity.json",
    )
    registry.verify(bot.bot_id)

    # 5. Show system prompt preview
    print("\n💬 Step 5: System prompt preview (first 400 chars)...")
    injector = PhilosophyPromptInjector(bot)
    print("-" * 70)
    print(injector.system_prompt[:400] + "...")

    # 6. Show example conversation structure
    print("\n\n📨 Example — inject into conversation:")
    print("-" * 70)
    messages = injector.inject_into_conversation([
        {"role": "user", "content": "I'm scared to quit my job and pursue my dream."}
    ])
    print(f"  Messages ready for Ollama: {len(messages)}")
    print(f"  [0] system: {len(messages[0]['content'])} chars (philosophy)")
    print(f"  [1] user:   {messages[1]['content']}")

    print("\n" + "=" * 70)
    print("✅ Done. Santiago is ready.")
    print(f"   Registry: {registry.stats()}")
    print("\nTo chat:")
    print("   injector = PhilosophyPromptInjector.from_file('data/bot_alchemist_identity.json')")
    print("   response = injector.chat('What should I do with my life?')")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
