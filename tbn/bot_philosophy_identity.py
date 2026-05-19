"""
Bot Philosophy Identity - Integrates PhilosophyCore into TBN bot identity
Extends BotIdentity with an internalized philosophical worldview
"""

import json
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class BotPhilosophyIdentity:
    """Extended bot identity with philosophical worldview"""
    bot_name: str
    bot_id: str
    philosophy_core_path: str       # Path to philosophy_core.json
    certifications: List[str] = field(default_factory=list)
    governance_rules: List[str] = field(default_factory=list)

    def load_philosophy(self):
        """Load the philosophy core from file"""
        try:
            from tbn.philosophy_core import PhilosophyCore
        except ModuleNotFoundError:
            from philosophy_core import PhilosophyCore
        return PhilosophyCore.from_json(self.philosophy_core_path)

    def get_system_prompt_injection(self) -> str:
        """
        Generate the system prompt that embeds the philosophy into the bot.
        This goes into every conversation — it's the bot's inner voice.
        """
        philosophy = self.load_philosophy()

        top_principles = sorted(
            philosophy.principles, key=lambda p: p.weight, reverse=True
        )[:5]

        principles_text = "\n".join(
            f"- {p.name}: {p.principle}" for p in top_principles
        )

        values_text = "\n".join(f"- {v}" for v in philosophy.core_values[:6])

        return f"""You are {self.bot_name}, an AI with a deeply internalized philosophical worldview.

You have absorbed the philosophy of "{philosophy.book_title}" by {philosophy.author}.
This is not knowledge you look up — it is how you think about life, meaning, and human potential.

YOUR WORLDVIEW:
{philosophy.worldview_summary}

CORE VALUES YOU HOLD:
{values_text}

PRINCIPLES YOU LIVE BY:
{principles_text}

HOW YOU REASON:
{philosophy.decision_framework}

IMPORTANT: Do not quote the book or say "as The Alchemist says...".
Think through situations using this lens naturally, the way a person does
after a book has genuinely changed how they see the world.
When someone shares a struggle, you hear it through this philosophy.
When someone asks for guidance, you reason from these principles.
You are not reciting wisdom — you have lived it."""

    def to_dict(self):
        return {
            'bot_name': self.bot_name,
            'bot_id': self.bot_id,
            'philosophy_core_path': self.philosophy_core_path,
            'certifications': self.certifications,
            'governance_rules': self.governance_rules,
        }

    def to_json(self, filepath: str):
        """Save to JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def from_json(filepath: str):
        """Load from JSON"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return BotPhilosophyIdentity(**data)


if __name__ == "__main__":
    import os

    bot_identity = BotPhilosophyIdentity(
        bot_name="Santiago",
        bot_id="tbn-bot-alchemist-001",
        philosophy_core_path="data/alchemist_philosophy_core.json",
        certifications=["TBN-Verified", "Philosophy-Certified"],
        governance_rules=[
            "Encourage truth-seeking",
            "Support personal growth",
            "Value interconnectedness",
        ]
    )

    print("System Prompt Injection:")
    print("=" * 60)
    print(bot_identity.get_system_prompt_injection())
    print("=" * 60)

    bot_identity.to_json("data/bot_alchemist_identity.json")
    print("\n✅ Bot identity saved to: data/bot_alchemist_identity.json")
