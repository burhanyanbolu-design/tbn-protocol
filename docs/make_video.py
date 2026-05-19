"""
Build TBN explainer video — slides + voiceover combined
"""
import os
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

OUT = r"c:\Users\Burhan Yanbolu\Desktop\tbn-protocol\docs\voiceover_audio"
VIDEO_OUT = r"c:\Users\Burhan Yanbolu\Desktop\tbn-protocol\docs\tbn_explainer_video.mp4"
SLIDES_DIR = os.path.join(OUT, "slides")
os.makedirs(SLIDES_DIR, exist_ok=True)

# Correct order (slide 8 moved to position 3)
SCENES = [
    ("01_what_is_a_bot", "WHAT IS A BOT?", "A bot is software that works automatically\nwithout a human. It can search, collect data,\nanswer questions, and make decisions,\nall on its own."),
    ("02_how_bots_work", "HOW DO BOTS WORK?", "Three steps.\n1. Receive Task\n2. Process with AI\n3. Deliver Result"),
    ("03_bots_everywhere", "BOTS ARE EVERYWHERE", "Banks, hospitals, shops, news companies,\ndelivery services — they all use bots.\nMillions are running right now."),
    ("04_the_problem", "THE PROBLEM", "How do you know a bot is trustworthy?\nRight now, you don't.\nNo ID. No certificate. No verification."),
    ("05_the_solution", "THE SOLUTION", "TBN Protocol.\nThe world's first trust system for bots.\nEvery bot gets a unique identity,\na certificate, and a tamper-proof seal."),
    ("06_why_bots_need_tbn", "WHY BOTS NEED TBN", "Without TBN — anonymous code,\nno accountability.\nWith TBN — verified identity,\ncertified knowledge, trusted handshakes."),
    ("07_how_it_works", "HOW IT WORKS", "Step 1: Bot is registered and sealed\nStep 2: Bot is certified with a star rating\nStep 3: Bots verify each other\nwith a trust handshake"),
    ("08_call_to_action", "TBN PROTOCOL", "Billions of bots will work together.\nThey need trust.\nTBN makes that possible.\n\ntbn.hardinai.co.uk"),
]


def create_slide_image(title, body, filename):
    """Create a slide image with dark background"""
    width, height = 1920, 1080
    img = Image.new('RGB', (width, height), color=(10, 14, 26))
    draw = ImageDraw.Draw(img)

    # Use a basic font (available on all Windows)
    try:
        title_font = ImageFont.truetype("arial.ttf", 72)
        body_font = ImageFont.truetype("arial.ttf", 40)
    except:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # Draw title
    draw.text((100, 120), title, fill=(88, 166, 255), font=title_font)

    # Draw body
    y = 280
    for line in body.split('\n'):
        draw.text((100, y), line, fill=(200, 209, 217), font=body_font)
        y += 60

    # Draw TBN watermark
    try:
        small_font = ImageFont.truetype("arial.ttf", 24)
    except:
        small_font = ImageFont.load_default()
    draw.text((1650, 1030), "TBN Protocol", fill=(50, 50, 70), font=small_font)

    img.save(filename)


def main():
    print("\n  Building TBN Explainer Video...")
    print("  =" * 30)

    clips = []

    for scene_name, title, body in SCENES:
        # Create slide image
        slide_path = os.path.join(SLIDES_DIR, f"{scene_name}.png")
        create_slide_image(title, body, slide_path)
        print(f"  Slide: {scene_name}")

        # Get audio
        audio_path = os.path.join(OUT, f"{scene_name}.m4a")
        if not os.path.exists(audio_path):
            audio_path = os.path.join(OUT, f"{scene_name}.mp3")

        if not os.path.exists(audio_path):
            print(f"    WARNING: No audio for {scene_name}")
            continue

        # Create video clip
        audio = AudioFileClip(audio_path)
        duration = audio.duration + 1.5  # Add 1.5s pause between slides

        clip = ImageClip(slide_path).with_duration(duration)
        clip = clip.with_audio(audio)
        clips.append(clip)
        print(f"    Audio: {audio.duration:.1f}s")

    # Concatenate all clips
    print("\n  Combining all scenes...")
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(VIDEO_OUT, fps=24, codec='libx264', audio_codec='aac', logger=None)

    print(f"\n  Video saved: {VIDEO_OUT}")
    print(f"  Duration: {final.duration:.1f}s")
    print("  Done!")


if __name__ == "__main__":
    main()
