import os
from moviepy import AudioFileClip

IN = r"c:\Users\Burhan Yanbolu\Desktop\tbn-protocol\docs\voiceover_audio"

files = sorted([f for f in os.listdir(IN) if f.endswith('.mp3')])

for f in files:
    mp3 = os.path.join(IN, f)
    m4a = os.path.join(IN, f.replace('.mp3', '.m4a'))
    print(f"  Converting: {f} -> .m4a")
    clip = AudioFileClip(mp3)
    clip.write_audiofile(m4a, codec='aac', logger=None)
    clip.close()
    print(f"    Done")

print(f"\n  All done! M4A files in: {IN}")
print("  Use these .m4a files in PowerPoint web.")
