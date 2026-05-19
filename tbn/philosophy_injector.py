"""
Philosophy Prompt Injector
Middleware that injects a bot's philosophical worldview into every conversation.
Sits between the user and the LLM — the bot always thinks through its philosophy.
"""

import json
import requests
from typing import Dict, List, Optional


class PhilosophyPromptInjector:
    """
    Injects philosophy into bot conversations.
    Use this in any conversation endpoint.
    """

    def __init__(self, bot_identity_path: str):
        from tbn.bot_philosophy_identity import BotPhilosophyIdentity
        self.bot_identity = BotPhilosophyIdentity.from_json(bot_identity_path)
        self.philosophy_system_prompt = self.bot_identity.get_system_prompt_injection()

    def inject_into_conversation(self, messages: List[Dict]) -> List[Dict]:
        """
        Add the philosophy as a system message at the start of every conversation.

        Usage:
            messages = [{"role": "user", "content": "What should I do with my life?"}]
            injected = injector.inject_into_conversation(messages)
            # Send to Ollama with injected philosophy
        """
        system_message = {
            "role": "system",
            "content": self.philosophy_system_prompt,
        }
        return [system_message] + messages

    def chat(self, user_message: str, history: List[Dict] = None,
             ollama_url: str = "http://localhost:11434") -> str:
        """
        Send a message to the philosophy-conditioned bot and get a response.

        Args:
            user_message: What the user said
            history: Previous conversation turns (optional)
            ollama_url: Ollama server URL

        Returns:
            Bot's response, reasoned through its philosophical worldview
        """
        messages = history or []
        messages = messages + [{"role": "user", "content": user_message}]
        injected = self.inject_into_conversation(messages)

        philosophy = self.bot_identity.load_philosophy()
        model = "llama3.2"  # Default — can be overridden

        try:
            response = requests.post(
                f"{ollama_url}/api/chat",
                json={"model": model, "messages": injected, "stream": False},
                timeout=120,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            return f"[Philosophy bot unavailable: {e}]"

    def get_philosophy_guidance(self, topic: str) -> str:
        """
        Get how this bot would approach a specific topic through its philosophy.
        Useful for debugging or showing what the bot's lens looks like.
        """
        philosophy = self.bot_identity.load_philosophy()
        top = sorted(philosophy.principles, key=lambda p: p.weight, reverse=True)[:3]

        lines = [f"How {self.bot_identity.bot_name} thinks about '{topic}' "
                 f"(through {philosophy.book_title}):\n"]
        for p in top:
            lines.append(f"  {p.name}: {p.application}")
        return "\n".join(lines)

    def get_bot_info(self) -> Dict:
        """Return info about this bot's philosophical identity"""
        philosophy = self.bot_identity.load_philosophy()
        return {
            "bot_name": self.bot_identity.bot_name,
            "bot_id": self.bot_identity.bot_id,
            "book": philosophy.book_title,
            "author": philosophy.author,
            "principles_count": len(philosophy.principles),
            "core_values": philosophy.core_values,
            "certifications": self.bot_identity.certifications,
        }


if __name__ == "__main__":
    import os

    identity_path = "data/bot_alchemist_identity.json"

    if not os.path.exists(identity_path):
        print("⚠️  Run tbn/bot_philosophy_identity.py first to generate the identity file.")
    else:
        injector = PhilosophyPromptInjector(identity_path)

        print("Bot Info:")
        print(json.dumps(injector.get_bot_info(), indent=2))

        print("\nPhilosophy Guidance on 'career change':")
        print(injector.get_philosophy_guidance("career change"))

        print("\nTesting conversation (requires Ollama running)...")
        response = injector.chat("I'm scared to quit my job and pursue my dream.")
        print(f"\nSantiago: {response}")
