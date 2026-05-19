"""
Setup a Philosophy Bot — end-to-end
Reads any book file (epub, html, pdf, txt), extracts the philosophy,
creates the bot identity, registers it in the TBN Philosophy Registry.

Usage:
    python tbn/setup_philosophy_bot.py
    python tbn/setup_philosophy_bot.py --file "C:/path/to/book.html" --name "Einstein"
"""

import argparse
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tbn.philosophy_core_complete import (
    PhilosophyCoreExtractor,
    BotPhilosophyIdentity,
    TBNPhilosophyRegistry,
    PhilosophyPromptInjector,
)


def setup_philosophy_bot(
    epub_path: str,
    bot_name: str,
    book_title: str,
    author: str,
    bot_id: str = None,
):
    os.makedirs("data", exist_ok=True)

    # ── Step 1: Read the book ─────────────────────────────────────────
    book_text = ""
    if epub_path and os.path.exists(epub_path):
        print(f"📖 Reading: {epub_path}")
        try:
            book_text = PhilosophyCoreExtractor.read_file(epub_path)
            print(f"✅ Read {len(book_text):,} characters")
        except Exception as e:
            print(f"⚠️  Could not read file ({e}), using fallback extraction")
    else:
        print("⚠️  No file provided, using built-in Alchemist philosophy")

    # ── Step 2: Extract philosophy ────────────────────────────────────
    print(f"\n🧠 Extracting philosophy from '{book_title}'...")
    extractor = PhilosophyCoreExtractor()
    bot_id = bot_id or f"tbn-bot-{bot_name.lower().replace(' ', '-')}-001"

    philosophy_core = extractor.extract(
        book_text=book_text,
        title=book_title,
        author=author,
        bot_id=bot_id,
    )

    core_path = f"data/{bot_name.lower()}_philosophy_core.json"
    philosophy_core.to_json(core_path)
    print(f"✅ Philosophy extracted: {len(philosophy_core.principles)} principles")

    # ── Step 3: Create bot identity ───────────────────────────────────
    print(f"\n🤖 Creating bot identity: {bot_name}")
    bot_identity = BotPhilosophyIdentity(
        bot_name=bot_name,
        bot_id=bot_id,
        philosophy_core=philosophy_core,
    )
    bot_identity.certifications = ["TBN-Verified", "Philosophy-Certified"]
    bot_identity.governance_rules = [
        "Encourage truth-seeking",
        "Support personal growth",
        "Value interconnectedness",
        "Reason from internalized wisdom, not recitation",
    ]

    identity_path = f"data/{bot_name.lower()}_bot_identity.json"
    bot_identity.to_json(identity_path)
    print(f"💾 Identity saved to: {identity_path}")

    # ── Step 4: Register in TBN Philosophy Registry ───────────────────
    print(f"\n📋 Registering in TBN Philosophy Registry...")
    registry = TBNPhilosophyRegistry()
    registry.register(
        bot_id=bot_id,
        bot_name=bot_name,
        book_title=book_title,
        author=author,
        philosophy_hash=philosophy_core.philosophy_hash,
        core_path=core_path,
        identity_path=identity_path,
    )
    registry.verify(bot_id)

    print(f"\n✅ {bot_name} is ready — {book_title} by {author}")
    print(f"   Principles: {len(philosophy_core.principles)}")

    return bot_identity, philosophy_core


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup a TBN Philosophy Bot")
    parser.add_argument("--file", default="", help="Path to book file (epub/html/pdf/txt)")
    parser.add_argument("--name", default="Santiago", help="Bot name")
    parser.add_argument("--title", default="The Alchemist", help="Book title")
    parser.add_argument("--author", default="Paulo Coelho", help="Author name")
    parser.add_argument("--bot-id", default=None, help="Custom bot ID")
    args = parser.parse_args()

    setup_philosophy_bot(
        epub_path=args.file,
        bot_name=args.name,
        book_title=args.title,
        author=args.author,
        bot_id=args.bot_id,
    )
