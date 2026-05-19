import asyncio
import edge_tts
import os
import subprocess

OUT = r"c:\Users\Burhan Yanbolu\Desktop\tbn-protocol\docs\voiceover_audio"
VOICE = "en-GB-SoniaNeural"
RATE = "-5%"

SCENES = [
    ("01_what_is_a_bot", "A bot is software that works automatically without a human. It can search, collect data, answer questions, and make decisions, all on its own. You use bots every day. Siri, website chat popups, bank fraud alerts. All bots."),
    ("02_how_bots_work", "Three steps. It receives a task. It processes it using rules or AI. It delivers the result. Simple."),
    ("03_bots_everywhere", "Banks, hospitals, shops, news companies, delivery services. They all use bots. Millions are running right now."),
    ("04_the_problem", "How do you know a bot is trustworthy? Right now, you do not. No ID. No certificate. No verification. Anyone can build a bot and pretend it is safe."),
    ("05_the_solution", "TBN Protocol. The worlds first trust system for bots. Every bot gets a unique identity, a certificate, and a tamper proof seal. Like a driving licence for AI."),
    ("06_why_bots_need_tbn", "Without TBN, anonymous code, no accountability. With TBN, verified identity, certified knowledge, trusted handshakes, and instant detection if tampered with."),
    ("07_how_it_works", "Step one, Bot is registered and sealed. Step two, Bot is certified with a star rating. Step three, Bots verify each other with a trust handshake. Valid certificate, connected. Invalid, denied."),
    ("08_call_to_action", "Billions of bots will work together. They need trust. TBN makes that possible. Visit tbn dot hardin ai dot co dot uk."),
]

async def main():
    # Generate as M4A (PowerPoint supports m4a/wma/wav/mp4)
    # edge-tts outputs mp3 by default, but PowerPoint Online supports mp3
    # For desktop PowerPoint, we'll use the Windows built-in converter
    for name, text in SCENES:
        mp3_path = os.path.join(OUT, f"{name}.mp3")
        m4a_path = os.path.join(OUT, f"{name}.m4a")
        print(f"  Recording: {name}...")
        c = edge_tts.Communicate(text, VOICE, rate=RATE)
        await c.save(mp3_path)

        # Try converting with PowerShell/Windows Media
        try:
            # Use Windows built-in to convert mp3 to m4a
            ps_cmd = f'''
Add-Type -AssemblyName PresentationCore
$player = New-Object System.Windows.Media.MediaPlayer
$player.Open([Uri]"{mp3_path}")
'''
            # Actually just rename to .m4a won't work
            # PowerPoint 2016+ DOES support MP3 - the error might be something else
            pass
        except:
            pass

        print(f"    Done: {mp3_path}")

    print("\n  All 8 MP3 files recorded!")
    print(f"  Folder: {OUT}")
    print("\n  NOTE: PowerPoint 2013+ supports MP3 directly.")
    print("  Insert → Audio → Audio on My PC → select the .mp3 file")
    print("  If it still fails, your PowerPoint version may need .wav")
    print("  In that case, use: https://cloudconvert.com/mp3-to-wav (free)")

asyncio.run(main())
