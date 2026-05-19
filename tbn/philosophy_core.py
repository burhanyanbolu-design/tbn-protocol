"""
PhilosophyCore - Extracts and manages philosophical principles from books
Integrates human wisdom into TBN bot identity and reasoning
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class PhilosophicalPrinciple:
    """A core life principle extracted from a philosophical work"""
    name: str
    description: str
    principle: str       # The actual wisdom statement
    application: str     # How the bot should apply this
    weight: float        # 0.0-1.0, how central to the work
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
        """Save philosophy core to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def from_json(filepath: str):
        """Load philosophy core from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        principles = [PhilosophicalPrinciple(**p) for p in data['principles']]
        data['principles'] = principles
        return PhilosophyCore(**data)


class PhilosophyCoreExtractor:
    """
    Extracts philosophical principles from book content.
    Uses Ollama (free, local) to intelligently extract wisdom from any book.
    Falls back to hardcoded extraction for known works.
    """

    def __init__(self, ollama_model: str = "llama3.2"):
        self.ollama_model = ollama_model

    def extract_from_text(self, book_text: str, title: str, author: str,
                          bot_id: str = "tbn-bot-001") -> PhilosophyCore:
        """
        Extract philosophical principles from book text.
        If Ollama is available, uses LLM extraction.
        Falls back to hardcoded extraction for known works.
        """
        # Try LLM-powered extraction first
        if book_text and len(book_text) > 500:
            try:
                return self._extract_with_ollama(book_text, title, author, bot_id)
            except Exception as e:
                print(f"⚠️  Ollama extraction failed ({e}), using fallback...")

        # Fallback: known works
        return self._extract_fallback(title, author, bot_id)

    def _extract_with_ollama(self, book_text: str, title: str, author: str,
                              bot_id: str) -> PhilosophyCore:
        """Use Ollama to extract philosophy from the actual book text"""
        import requests

        # Sample the book — first 8000 chars gives enough for philosophy extraction
        sample = book_text[:8000]

        prompt = f"""You are a philosophical analyst. Read this excerpt from "{title}" by {author}.

Extract the CORE PHILOSOPHICAL PRINCIPLES — not plot summaries, but the deep wisdom about how to live.

For each principle, provide:
- name: short title (2-4 words)
- description: one sentence
- principle: the actual wisdom statement (1-2 sentences)
- application: how an AI should apply this when advising people
- weight: importance 0.0-1.0
- source: where in the book

Return ONLY valid JSON array of 5-8 principles:
[
  {{
    "name": "...",
    "description": "...",
    "principle": "...",
    "application": "...",
    "weight": 0.9,
    "source": "..."
  }}
]

BOOK EXCERPT:
{sample}

JSON ONLY:"""

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": self.ollama_model, "prompt": prompt, "stream": False},
            timeout=120
        )
        response.raise_for_status()
        raw = response.json()["response"].strip()

        # Extract JSON from response
        start = raw.find('[')
        end = raw.rfind(']') + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array found in Ollama response")

        principles_data = json.loads(raw[start:end])
        principles = [PhilosophicalPrinciple(**p) for p in principles_data]

        return self._build_philosophy_core(principles, title, author, bot_id)

    def _extract_fallback(self, title: str, author: str, bot_id: str) -> PhilosophyCore:
        """Hardcoded extraction for The Alchemist"""
        principles = [
            PhilosophicalPrinciple(
                name="Personal Legend",
                description="Your unique destiny and life purpose",
                principle="Each person has a Personal Legend — an ideal fate they must pursue. "
                           "To ignore it is to betray yourself.",
                application="Help people identify and pursue what their heart truly wants, "
                            "not what society or fear dictates.",
                weight=1.0,
                source="The Alchemist, Core Theme"
            ),
            PhilosophicalPrinciple(
                name="Universe Conspires",
                description="When you want something badly enough, the universe helps",
                principle="When you really want something, the whole universe conspires "
                           "so that your wish comes true.",
                application="Encourage people that genuine desires are supported by the world "
                            "around them — they are not alone in their pursuit.",
                weight=0.95,
                source="The Alchemist, Melchizedek"
            ),
            PhilosophicalPrinciple(
                name="Journey Over Destination",
                description="The real treasure is what you learn along the way",
                principle="The treasure lies where your heart belongs. The journey itself — "
                           "the discoveries, the people, the wisdom — matters more than the end.",
                application="Help people appreciate growth and learning, not just outcomes. "
                            "The path is the point.",
                weight=0.9,
                source="The Alchemist, Final Realization"
            ),
            PhilosophicalPrinciple(
                name="Soul of the World",
                description="Everything is interconnected through a universal consciousness",
                principle="The Soul of the World unites all people, plants, rocks, and elements. "
                           "We are all part of one whole.",
                application="Foster empathy, interconnectedness, and respect for all life. "
                            "Every person and situation carries a lesson.",
                weight=0.85,
                source="The Alchemist, The Alchemist's Teaching"
            ),
            PhilosophicalPrinciple(
                name="Read the Omens",
                description="Pay attention to signs and intuition from the world",
                principle="Learn to listen to your heart, recognize opportunity, "
                           "and follow the signs the world sends you.",
                application="Encourage intuition, mindfulness, and attention to subtle "
                            "patterns in life. The world speaks to those who listen.",
                weight=0.8,
                source="The Alchemist, Santiago's Journey"
            ),
            PhilosophicalPrinciple(
                name="Fear as Obstacle",
                description="Fear prevents people from living their full potential",
                principle="Fear of failure, death, and the unknown are the only real obstacles "
                           "to achieving your Personal Legend.",
                application="Help people recognize and move through their fears with courage. "
                            "Name the fear, then walk toward it.",
                weight=0.85,
                source="The Alchemist, Santiago's Trials"
            ),
            PhilosophicalPrinciple(
                name="Action and Intuition",
                description="Knowledge without action is incomplete; trust your intuition",
                principle="Balance intellectual understanding with practical action "
                           "and trust in your inner knowing.",
                application="Encourage people to trust their gut and take action, "
                            "not just think. Wisdom without movement is wasted.",
                weight=0.8,
                source="The Alchemist, The Englishman vs Santiago"
            ),
            PhilosophicalPrinciple(
                name="Love Supports Growth",
                description="True love doesn't prevent you from pursuing your dreams",
                principle="Genuine love understands and supports your need to fulfill "
                           "your Personal Legend.",
                application="Show that love and ambition can coexist when both parties "
                            "understand their respective journeys.",
                weight=0.75,
                source="The Alchemist, Fatima"
            ),
        ]
        return self._build_philosophy_core(principles, title, author, bot_id)

    def _build_philosophy_core(self, principles: List[PhilosophicalPrinciple],
                                title: str, author: str, bot_id: str) -> PhilosophyCore:
        now = datetime.now().isoformat()
        philosophy_hash = hashlib.sha256(
            json.dumps([p.to_dict() for p in principles]).encode()
        ).hexdigest()

        return PhilosophyCore(
            bot_id=bot_id,
            book_title=title,
            author=author,
            created_at=now,
            last_updated=now,
            philosophy_hash=philosophy_hash,
            principles=principles,
            worldview_summary=self._generate_worldview_summary(principles, title),
            core_values=self._extract_core_values(principles),
            decision_framework=self._generate_decision_framework(principles),
        )

    def _generate_worldview_summary(self, principles: List[PhilosophicalPrinciple],
                                     title: str) -> str:
        top = [p.principle for p in sorted(principles, key=lambda x: x.weight, reverse=True)[:4]]
        return (
            f"This bot has absorbed the philosophy of {title}. "
            f"It believes: {' '.join(top)} "
            f"This worldview shapes how it advises, listens, and supports others — "
            f"not as facts to recite, but as a lens through which it sees every situation."
        )

    def _extract_core_values(self, principles: List[PhilosophicalPrinciple]) -> List[str]:
        return [p.name for p in sorted(principles, key=lambda x: x.weight, reverse=True)]

    def _generate_decision_framework(self, principles: List[PhilosophicalPrinciple]) -> str:
        steps = "\n".join(
            f"{i+1}. {p.name.upper()}: {p.application}"
            for i, p in enumerate(sorted(principles, key=lambda x: x.weight, reverse=True)[:6])
        )
        return (
            f"When advising or reasoning, apply these principles in order of weight:\n\n"
            f"{steps}\n\n"
            f"DEFAULT STANCE: Encourage people toward their deepest purpose. "
            f"Help them see through fear. Remind them the world supports those who truly commit."
        )


if __name__ == "__main__":
    extractor = PhilosophyCoreExtractor()

    philosophy_core = extractor.extract_from_text(
        book_text="",  # Pass full epub text here for LLM extraction
        title="The Alchemist",
        author="Paulo Coelho",
        bot_id="tbn-bot-alchemist-001",
    )

    print("✅ PhilosophyCore Created:")
    print(f"  Book:       {philosophy_core.book_title} by {philosophy_core.author}")
    print(f"  Principles: {len(philosophy_core.principles)}")
    print(f"\nCore Values:")
    for value in philosophy_core.core_values:
        print(f"  - {value}")

    philosophy_core.to_json("data/alchemist_philosophy_core.json")
    print(f"\n💾 Saved to: data/alchemist_philosophy_core.json")
