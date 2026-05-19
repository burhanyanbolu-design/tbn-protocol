"""
Quick test — talk to Santiago (The Alchemist philosophy bot)
Run from project root: python test_philosophy_bot.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tbn.philosophy_injector import PhilosophyPromptInjector

# Load Santiago
injector = PhilosophyPromptInjector("data/santiago_bot_identity.json")

# Show bot info
info = injector.get_bot_info()
print(f"Bot: {info['bot_name']} | Book: {info['book']} by {info['author']}")
print(f"Principles: {info['principles_count']} | Values: {', '.join(info['core_values'][:3])}...")
print("=" * 60)

# Test 1: inject_into_conversation (just shows the structure)
messages = injector.inject_into_conversation([
    {"role": "user", "content": "I'm afraid to pursue my dreams"}
])
print(f"Messages ready to send to Ollama: {len(messages)} total")
print(f"System prompt length: {len(messages[0]['content'])} chars")
print(f"User message: {messages[1]['content']}")
print("=" * 60)

# Test 2: actually chat (requires Ollama running)
print("Sending to Ollama...")
response = injector.chat("I'm afraid to pursue my dreams")
print(f"\nSantiago: {response}")
