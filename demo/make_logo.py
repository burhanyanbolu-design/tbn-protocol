"""Generate TBN Protocol logo (256x256 PNG) and product image (800x450 PNG)"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# --- Logo 256x256 ---
logo = Image.new('RGB', (256, 256), '#0a0818')
d = ImageDraw.Draw(logo)

# Circle background
d.ellipse([28, 28, 228, 228], fill='#1a1440', outline='#40ffbb', width=3)
d.ellipse([40, 40, 216, 216], fill=None, outline='#28d9a0', width=1)

# TBN text
try:
    font = ImageFont.truetype("arial.ttf", 72)
    font_small = ImageFont.truetype("arial.ttf", 20)
except:
    font = ImageFont.load_default()
    font_small = font

# Draw TBN
bbox = d.textbbox((0, 0), "TBN", font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
d.text(((256-tw)//2, (256-th)//2 - 15), "TBN", fill='#40ffbb', font=font)

# Draw "PROTOCOL" below
bbox2 = d.textbbox((0, 0), "PROTOCOL", font=font_small)
tw2 = bbox2[2] - bbox2[0]
d.text(((256-tw2)//2, 165), "PROTOCOL", fill='#9a93e8', font=font_small)

# Glow dots at cardinal points
for pos in [(128, 30), (128, 226), (30, 128), (226, 128)]:
    d.ellipse([pos[0]-4, pos[1]-4, pos[0]+4, pos[1]+4], fill='#40ffbb')

logo.save(os.path.join(OUT, 'tbn-logo-256.png'))
print("✅ Logo saved: tbn-logo-256.png")

# --- Product Image 800x450 ---
prod = Image.new('RGB', (800, 450), '#0a0818')
d2 = ImageDraw.Draw(prod)

# Background gradient-ish
for y in range(450):
    r = int(10 + (26-10) * (1 - abs(y-225)/225))
    g = int(8 + (20-8) * (1 - abs(y-225)/225))
    b = int(24 + (64-24) * (1 - abs(y-225)/225))
    d2.line([(0, y), (800, y)], fill=(r, g, b))

# Central content area
d2.rounded_rectangle([40, 30, 760, 420], radius=16, fill='#1a1440', outline='#3C3489')

# Title
try:
    title_font = ImageFont.truetype("arial.ttf", 36)
    sub_font = ImageFont.truetype("arial.ttf", 18)
    body_font = ImageFont.truetype("arial.ttf", 14)
    mono_font = ImageFont.truetype("cour.ttf", 12)
except:
    title_font = ImageFont.load_default()
    sub_font = title_font
    body_font = title_font
    mono_font = title_font

d2.text((80, 60), "TBN Protocol", fill='#40ffbb', font=title_font)
d2.text((80, 105), "The Certificate Authority for AI Agents", fill='#9a93e8', font=sub_font)

# Feature bullets
features = [
    "🪪  Verified cryptographic identity for every AI agent",
    "📝  Signed receipt for every autonomous decision (RSA-PSS SHA-256)",
    "✅  Offline verification — no trust required",
    "📊  1,300+ production receipts issued",
    "🔓  Open source (AGPL-3.0) · pip install tbn-protocol",
]
y = 160
for f in features:
    d2.text((100, y), f, fill='#e4e4e7', font=body_font)
    y += 32

# Code snippet box
d2.rounded_rectangle([80, 330, 720, 400], radius=8, fill='#0a0818', outline='#3C3489')
d2.text((100, 342), "GET /api/v1/verify/tbn_vr_0af954b9c2bf...", fill='#4ade80', font=mono_font)
d2.text((100, 362), '{"verified": true, "signature_valid": true, "agent": "shango-mid-001"}', fill='#71717a', font=mono_font)

# URL
d2.text((80, 410), "https://tbn.hardinai.co.uk", fill='#71717a', font=body_font)
d2.text((500, 410), "Live in Production · EU AI Act Ready", fill='#74e3bc', font=body_font)

prod.save(os.path.join(OUT, 'tbn-product-800x450.png'))
print("✅ Product image saved: tbn-product-800x450.png")
