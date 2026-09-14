#!/usr/bin/env python3
from pathlib import Path
import random
import subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageOps

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

# Safe 256x128 HOME Menu banner.
#
# This is deliberately the standard bannertool 2D banner path first.  It gives
# the installed CIA real artwork + audio without relying on an untested custom
# extended CGFX banner.  The later microphone-reactive 3D experiment can be
# layered on once this baseline is hardware-confirmed.
bg_path = ROOT / "assets" / "backgrounds" / "menu_palace_exterior.png"
if bg_path.exists():
    banner = ImageOps.fit(load_rgba(bg_path), (256,128), method=Image.Resampling.LANCZOS)
else:
    banner = Image.new("RGBA",(256,128),(12,6,20,255))

banner.alpha_composite(Image.new("RGBA",(256,128),(4,0,12,80)))

# Kandrakar Heart in the middle with a soft magical halo.
if heart_path.exists():
    heart = load_rgba(heart_path)
    heart.thumbnail((74,74), Image.Resampling.LANCZOS)
    hx, hy = 111 - heart.width//2, 64 - heart.height//2

    alpha = heart.getchannel("A")
    glow = Image.new("RGBA", heart.size, (210,105,255,0))
    glow.putalpha(alpha.filter(ImageFilter.GaussianBlur(7)))
    halo = Image.new("RGBA",(256,128),(0,0,0,0))
    halo.alpha_composite(glow, (hx,hy))
    halo = halo.filter(ImageFilter.GaussianBlur(4))
    banner.alpha_composite(halo)
    banner.alpha_composite(heart,(hx,hy))

# Phobos foreground on the right.
phobos_path = ROOT / "assets" / "menu" / "phobos" / "menu_body_opaque.png"
if phobos_path.exists():
    ph = load_rgba(phobos_path)
    ph.thumbnail((100,121), Image.Resampling.LANCZOS)

    # Remove only the pale studio-like canvas while keeping costume blacks.
    px = ph.load()
    for y in range(ph.height):
        for x in range(ph.width):
            r,g,b,a = px[x,y]
            if min(r,g,b) > 242 and max(r,g,b)-min(r,g,b) < 12:
                px[x,y] = (r,g,b,0)
    banner.alpha_composite(ph,(256-ph.width-3,128-ph.height))

# Small title card stays readable even when the HOME Menu tilts the banner.
draw = ImageDraw.Draw(banner)
draw.rounded_rectangle((5,8,86,47), radius=6,
                       fill=(7,3,15,185), outline=(205,135,244,235), width=2)
draw.text((12,15), "W.I.T.C.H.", fill=(230,186,255,255))
draw.text((12,31), "TETRIS 3DS", fill=(255,250,255,255))

# Deterministic magical particles around Heart/Phobos.  They are intentionally
# bright enough to stay visible on the original 3DS top screen.
rng = random.Random(0x57495443)
particle_layer = Image.new("RGBA",(256,128),(0,0,0,0))
pd = ImageDraw.Draw(particle_layer)
for i in range(34):
    angle = rng.random() * 6.28318530718
    radius = rng.randint(24,70)
    x = int(112 + __import__("math").cos(angle) * radius)
    y = int(64 + __import__("math").sin(angle) * radius * 0.55)
    if 4 <= x < 252 and 4 <= y < 124:
        size = rng.choice((1,1,2,2,3))
        col = rng.choice(((245,190,255,205),(180,115,255,190),
                          (255,225,145,200),(125,215,255,185)))
        pd.ellipse((x-size,y-size,x+size,y+size),fill=col)

# A few stylised lightning strokes near Phobos.
for pts in (
    [(205,36),(197,49),(207,52),(197,70)],
    [(227,22),(218,36),(227,39),(216,55)],
    [(214,74),(205,86),(215,90),(208,105)],
):
    pd.line(pts,fill=(220,155,255,205),width=2)

particle_layer = particle_layer.filter(ImageFilter.GaussianBlur(0.35))
banner.alpha_composite(particle_layer)
banner.convert("RGB").save(OUT / "banner.png", quality=95)

# The user-provided ~2.95 s MP3 is stored with the source tree.  Trim it to
# 2.90 s and convert to the conservative bannertool format: PCM16, stereo,
# 44.1 kHz.  The tiny fade avoids a hard click at the 3-second banner limit.
jingle_src = OUT / "banner_jingle.mp3"
banner_wav = OUT / "banner.wav"
if jingle_src.exists():
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(jingle_src),
        "-af", "atrim=duration=2.90,asetpts=N/SR/TB,afade=t=out:st=2.78:d=0.12",
        "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le",
        str(banner_wav),
    ], check=True)
else:
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "2.90", "-c:a", "pcm_s16le",
        str(banner_wav),
    ], check=True)

print(f"[cia] generated icon/banner/jingle metadata in {OUT}")
