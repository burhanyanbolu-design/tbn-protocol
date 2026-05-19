import asyncio
import edge_tts
import os

OUT = r"c:\Users\Burhan Yanbolu\Desktop\tbn-protocol\docs\voiceover_audio"
os.makedirs(OUT, exist_ok=True)

VOICE = "en-GB-SoniaNeural"
RATE = "-5%"

SCENES = [
    ("01_what_is_a_bot", "A bot is software that works automatically without a human. It can search, collect data, answer questions, and make decisions, all on its own. You use bots every day. Siri, website chat popups, bank fraud alerts. All bots."),
    ("02_how_bots_work", "Three steps. It receives a task. It processes it using rules or AI. It delivers the result. Simple."),
    ("03_bots_everywhere", "Banks, hospitals, shops, news companies, delivery services. They all use bots. Millions are running right now."),
    ("04_the_problem", "How do you know a bot is trustworthy? Right now, you don't. No ID. No certificate. No verification. Anyone can build a bot and pretend it's safe."),
    ("05_the_solution", "TBN Protocol. The world's first trust system for bots. Every bot gets a unique identity, a certificate, and a tamper-proof seal. Like a driving licence for AI."),
    ("06_why_bots_need_tbn", "Without TBN, anonymous code, no accountability. With TBN, verified identity, certified knowledge, trusted handshakes, and instant detection if tampered with."),
    ("07_how_it_works", "Step one: Bot is registered and sealed. Step two: Bot is certified with a star rating. Step three: Bots verify each other with a trust handshake. Valid certificate, connected. Invalid, denied."),
    ("08_call_to_action", "Billions of bots will work together. They need trust. TBN makes that possible. Visit tbn.hardinai.co.uk."),
]

async def main():
    for name, text in SCENES:
        path = os.path.join(OUT, f"{name}.mp3")
        print(f"  Recording: {name}...")
        c = edge_tts.Communicate(text, VOICE, rate=RATE)
        await c.save(path)
        print(f"    Done: {path}")
    print("\n  All 8 scenes recorded!")
    print(f"  Files in: {OUT}")

asyncio.run(main())
