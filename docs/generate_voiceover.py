"""
Generate voiceover audio files for the Powtoon video
Uses edge-tts (Sonia neural voice) — free, natural sounding
"""
import asyncio
import edge_tts
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "voiceover_audio")
os.makedirs(OUTPUT_DIR, exist_ok=True)

VOICE = "en-GB-SoniaNeural"
RATE = "-5%"  # Slightly slower for clarity

# Script broken into scenes for easier editing in Powtoon
SCENES = {
    "01_what_is_a_bot": """
A bot is a piece of software that does tasks automatically, without a human clicking buttons.
Think of it like a digital worker. It can search the internet, collect data, answer questions, make decisions, or talk to other systems, all on its own, 24 hours a day.
You already use bots every day without realising it. When you ask Siri a question, that's a bot. When a website has a chat popup saying how can I help, that's a bot. When your bank sends you a fraud alert, a bot detected it.
""",

    "02_how_bots_work": """
A bot works in three steps.
First, it receives a task. Maybe check the weather, or find the cheapest flight, or reply to this customer.
Second, it processes the task. It follows rules, searches databases, or uses artificial intelligence to figure out the answer.
Third, it delivers the result. It sends you a message, updates a spreadsheet, or talks to another bot.
Simple bots follow fixed rules, like if someone says hello, say hello back. Smart bots learn and adapt. They get better over time.
""",

    "03_bots_everywhere": """
Today, bots are everywhere.
Banks use bots to detect fraud. Hospitals use bots to book appointments. Shops use bots to recommend products. News companies use bots to write articles. Delivery companies use bots to plan routes.
There are millions of bots operating right now, and that number is growing every day.
""",

    "04_the_problem": """
But here's the problem.
How do you know if a bot is trustworthy? How do you know it's not stealing data, spreading lies, or pretending to be something it's not?
Right now, you don't. There's no system to verify bots. No ID. No certificate. No way to check if a bot is legitimate or dangerous.
It's like the internet before HTTPS. Anyone could pretend to be anyone.
""",

    "05_the_solution": """
That's where TBN Protocol comes in.
TBN stands for Trusted Bot Network. It's the world's first trust infrastructure for AI bots.
Every bot on our network gets a unique identity, like a digital passport. It gets certified, sealed, and verified. Other bots can check: is this bot real? Is it safe? Can I trust it?
Think of it like a driving licence for bots. You wouldn't get in a taxi with no licence plate. Why would you trust a bot with no certificate?
""",

    "06_why_bots_need_tbn": """
Without TBN, a bot is just anonymous code. No accountability. No verification. No trust.
With TBN, a bot has a verified identity that can't be faked. A certificate showing what it knows and where that knowledge came from. The ability to handshake with other trusted bots. And a tamper-proof seal. If anyone modifies it, the network knows immediately.
Companies want to know the bots they're using are safe. TBN gives them that confidence.
""",

    "07_how_it_works": """
Here's how it works in three steps.
Step one: A bot is created and registered on the TBN network. It gets a unique ID and a cryptographic seal.
Step two: The bot is certified. We verify what it can do, what data it has, and how intelligent it is, rated from one to five stars.
Step three: When that bot needs to work with another bot or a company's system, they do a trust handshake. Both sides verify each other's identity instantly. If the certificate is valid, they connect. If not, access denied.
No fakes. No imposters. No unverified bots.
""",

    "08_call_to_action": """
The future of AI is billions of bots working together. But that only works if they can trust each other.
TBN Protocol makes that possible.
Visit tbn dot hardin ai dot co dot uk to learn more.
""",
}


async def generate_all():
    """Generate all voiceover audio files"""
    print("\n  Generating voiceover audio files...")
    print(f"  Voice: {VOICE}")
    print(f"  Output: {OUTPUT_DIR}\n")

    for scene_name, text in SCENES.items():
        output_path = os.path.join(OUTPUT_DIR, f"{scene_name}.mp3")
        print(f"  Generating: {scene_name}...")

        communicate = edge_tts.Communicate(text.strip(), VOICE, rate=RATE)
        await communicate.save(output_path)

        # Get file size
        size_kb = os.path.getsize(output_path) / 1024
        print(f"    ✓ Saved ({size_kb:.0f} KB)")

    # Also generate full version
    print("\n  Generating full voiceover (all scenes combined)...")
    full_text = "\n\n".join(text.strip() for text in SCENES.values())
    full_path = os.path.join(OUTPUT_DIR, "full_voiceover.mp3")
    communicate = edge_tts.Communicate(full_text, VOICE, rate=RATE)
    await communicate.save(full_path)
    size_mb = os.path.getsize(full_path) / (1024 * 1024)
    print(f"    ✓ Full voiceover saved ({size_mb:.1f} MB)")

    print(f"\n  Done! All files in: {OUTPUT_DIR}")
    print("  Import these MP3s into Powtoon for each scene.\n")


if __name__ == "__main__":
    asyncio.run(generate_all())
