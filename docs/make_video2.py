import os
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

OUT = r"c:\Users\Burhan Yanbolu\Desktop\tbn-protocol\docs\voiceover_audio"
VIDEO_OUT = r"c:\Users\Burhan Yanbolu\Desktop\tbn-protocol\docs\tbn_explainer_video.mp4"
SLIDES_DIR = os.path.join(OUT, "slides")
os.makedirs(SLIDES_DIR, exist_ok=True)

FONT_PATH = "C:/Windows/Fonts/arial.ttf"

SCENES = [
    ("01_what_is_a_bot", "WHAT IS A BOT?", "A bot is software that works automatically\nwithout a human. It can search, collect data,\nanswer questions, and make decisions,\nall on its own."),
    ("02_how_bots_work", "HOW DO BOTS WORK?", "Three steps.\n\n1. Receive Task\n2. Process with AI\n3. Deliver Result\n\nSimple."),
    ("03_bots_everywhere", "BOTS ARE EVERYWHERE", "Banks, hospitals, shops, news companies,\ndelivery services — they all use bots.\n\nMillions are running right now."),
    ("04_the_problem", "THE PROBLEM", "How do you know a bot is trustworthy?\n\nRight now, you don't.\nNo ID. No certificate. No verification.\nAnyone can build a bot and pretend it's safe."),
    ("05_the_solution", "THE SOLUTION — TBN", "TBN Protocol.\nThe world's first trust system for bots.\n\nEvery bot gets a unique identity,\na certificate, and a tamper-proof seal.\n\nLike a driving licence for AI."),
    ("06_why_bots_need_tbn", "WHY BOTS NEED TBN", "Without TBN — anonymous code,\nno accountability.\n\nWith TBN — verified identity,\ncertified knowledge, trusted handshakes,\nand instant detection if tampered with."),
    ("07_how_it_works", "HOW IT WORKS", "Step 1: Bot is registered and sealed\nStep 2: Bot is certified with a star rating\nStep 3: Bots verify each other\n         with a trust handshake\n\nValid certificate — connected.\nInvalid — denied."),
    ("08_call_to_action", "TBN PROTOCOL", "Billions of bots will work together.\nThey need trust.\n\nTBN makes that possible.\n\ntbn.hardinai.co.uk"),
]


def create_slide(title, body, filepath):
    img = Image.new('RGB', (1920, 1080), (10, 14, 26))
    draw = ImageDraw.Draw(img)
    title_font = ImageFont.truetype(FONT_PATH, 72)
    body_font = ImageFont.truetype(FONT_PATH, 42)
    small_font = ImageFont.truetype(FONT_PATH, 22)

    draw.text((100, 100), title, fill=(88, 166, 255), font=title_font)

    y = 260
    for line in body.split('\n'):
        draw.text((100, y), line, fill=(200, 209, 217), font=body_font)
        y += 58

    draw.text((1680, 1040), "TBN Protocol", fill=(40, 50, 70), font=small_font)
    img.save(filepath)


print("\n  Building TBN Explainer Video...")
clips = []

for name, title, body in SCENES:
    slide_path = os.path.join(SLIDES_DIR, f"{name}.png")
    create_slide(title, body, slide_path)

    audio_path = os.path.join(OUT, f"{name}.m4a")
    if not os.path.exists(audio_path):
        audio_path = os.path.join(OUT, f"{name}.mp3")

    audio = AudioFileClip(audio_path)
    duration = audio.duration + 1.0

    clip = ImageClip(slide_path).with_duration(duration).with_audio(audio)
    clips.append(clip)
    print(f"  {name}: {audio.duration:.1f}s")

print("\n  Rendering video...")
final = concatenate_videoclips(clips, method="compose")
final.write_videofile(VIDEO_OUT, fps=24, codec='libx264', audio_codec='aac', logger=None)
print(f"\n  Done! Video: {VIDEO_OUT}")
print(f"  Duration: {final.duration:.0f}s")
