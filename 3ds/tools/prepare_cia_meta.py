#!/usr/bin/env python3
from pathlib import Path
import wave
import struct
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "3ds" / "cia"
OUT.mkdir(parents=True, exist_ok=True)

def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")

# HOME Menu icon (48x48): Kandrakarian heart on a dark purple field.
icon = Image.new("RGBA", (48, 48), (19, 8, 30, 255))
heart_path = ROOT / "assets" / "effects" / "heart_kandrakar.png"
if heart_path.exists():
    heart = load_rgba(heart_path)
    heart.thumbnail((38, 38), Image.Resampling.LANCZOS)
    icon.alpha_composite(heart, ((48-heart.width)//2, (48-heart.height)//2))
ImageDraw.Draw(icon).rectangle((0,0,47,47), outline=(196,126,238,255), width=2)
icon.save(OUT / "icon.png")

# 256x128 HOME Menu banner: original palace background + Phobos foreground.
bg_path = ROOT / "assets" / "backgrounds" / "menu_palace_exterior.png"
if bg_path.exists():
    bg = ImageOps.fit(load_rgba(bg_path), (256,128), method=Image.Resampling.LANCZOS)
else:
    bg = Image.new("RGBA",(256,128),(12,6,20,255))

shade = Image.new("RGBA",(256,128),(0,0,0,72))
bg.alpha_composite(shade)

phobos_path = ROOT / "assets" / "menu" / "phobos" / "menu_body_opaque.png"
if phobos_path.exists():
    ph = load_rgba(phobos_path)
    ph.thumbnail((104,122), Image.Resampling.LANCZOS)
    # Make near-white connected-ish background transparent enough for banner use.
    px = ph.load()
    for y in range(ph.height):
        for x in range(ph.width):
            r,g,b,a = px[x,y]
            if min(r,g,b) > 242 and max(r,g,b)-min(r,g,b) < 12:
                px[x,y] = (r,g,b,0)
    bg.alpha_composite(ph, (256-ph.width-6, 128-ph.height))

draw = ImageDraw.Draw(bg)
draw.rounded_rectangle((7,10,166,112), radius=8, fill=(8,4,14,186), outline=(191,121,230,240), width=2)
draw.text((18,24), "W.I.T.C.H.", fill=(225,176,255,255))
draw.text((18,48), "TETRIS 3DS", fill=(255,250,255,255))
draw.text((18,82), "PHOBOS EDITION", fill=(192,137,225,255))
bg.convert("RGB").save(OUT / "banner.png")

# Bannertool requires WAV audio for a banner. Keep it intentionally silent:
# in-game music remains the actual original soundtrack.
rate = 22050
frames = rate
with wave.open(str(OUT / "banner.wav"), "wb") as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(rate)
    silent = struct.pack("<hh", 0, 0)
    wav.writeframes(silent * frames)

print(f"[cia] generated metadata in {OUT}")
