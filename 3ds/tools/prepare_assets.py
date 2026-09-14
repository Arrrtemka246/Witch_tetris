#!/usr/bin/env python3
"""Prepare W.I.T.C.H. Tetris assets for Nintendo 3DS.

The desktop game remains the source of truth. This script creates a compact
RomFS for the native 3DS port:
- PNG/JPEG -> tex3ds .t3x (ETC1/ETC1A4 or RGBA5551 for tetromino fragments)
- MP3/WAV are copied losslessly; MP3 is decoded on-device with mpg123
- Phase-I tetromino artwork is split into 24x24 fragments so locked pieces keep
  the same "character breaks apart when lines clear" behaviour as main.py.

Profiles:
  core - content used by the current 3DS build (fast CI/test package)
  full - additionally converts every image/audio asset into a browsable data pack
"""

from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

try:
    from PIL import Image, ImageOps
except ImportError as exc:
    raise SystemExit("Pillow is required: python3 -m pip install Pillow") from exc

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
DS = ROOT / "3ds"
ROMFS = DS / "romfs"
WORK = DS / ".asset_build"
GFX = ROMFS / "gfx"
AUDIO = ROMFS / "audio"

KIND_ORDER = ("I", "O", "T", "S", "Z", "J", "L")
BASE = {
    "I": ((0,0),(0,1),(0,2),(0,3)),
    "O": ((0,0),(1,0),(0,1),(1,1)),
    "T": ((0,0),(1,0),(2,0),(1,1)),
    "S": ((0,0),(1,0),(1,1),(2,1)),
    "Z": ((1,0),(2,0),(0,1),(1,1)),
    "J": ((0,0),(0,1),(1,1),(2,1)),
    "L": ((2,0),(0,1),(1,1),(2,1)),
}

CORE_IMAGES = {
    # Menu / game backgrounds
    "bg_menu": ("backgrounds/menu_palace_exterior.png", "cover"),
    "bg_phase0": ("backgrounds/phase_0_99_throne.png", "cover"),
    "bg_phase1": ("backgrounds/phase_100_199_unstable.png", "cover"),
    "bg_phase2": ("backgrounds/phase_200_plus_liberated.png", "cover"),

    # Intro / story
    "intro_castle": ("cutscenes/intro/castle_exterior.png", "cover"),
    "intro_throne": ("cutscenes/intro/throne_hall.png", "cover"),
    "intro_phobos": ("cutscenes/intro/processed/phobos_normal.png", "actor"),
    "intro_phobos_cast": ("cutscenes/intro/processed/phobos_cast.png", "actor"),
    "intro_will": ("cutscenes/intro/processed/will_normal.png", "actor"),
    "intro_will_final": ("cutscenes/intro/processed/will_final.png", "actor"),
    "intro_irma": ("cutscenes/intro/processed/irma_normal.png", "actor"),
    "intro_taranee": ("cutscenes/intro/processed/taranee_normal.png", "actor"),
    "intro_cornelia": ("cutscenes/intro/processed/cornelia_normal.png", "actor"),
    "intro_haylin": ("cutscenes/intro/processed/haylin_normal.png", "actor"),
    "intro_caleb": ("cutscenes/intro/processed/caleb_normal.png", "actor"),
    "intro_blunk": ("cutscenes/intro/processed/blunk_normal.png", "actor"),
    "intro_will_t1": ("cutscenes/intro/processed/will_t1.png", "actor"),
    "intro_will_t2": ("cutscenes/intro/processed/will_t2.png", "actor"),
    "intro_will_final": ("cutscenes/intro/processed/will_final.png", "actor"),
    "intro_irma_t1": ("cutscenes/intro/processed/irma_t1.png", "actor"),
    "intro_irma_t2": ("cutscenes/intro/processed/irma_t2.png", "actor"),
    "intro_irma_final": ("cutscenes/intro/processed/irma_final.png", "actor"),
    "intro_taranee_t1": ("cutscenes/intro/processed/taranee_t1.png", "actor"),
    "intro_taranee_t2": ("cutscenes/intro/processed/taranee_t2.png", "actor"),
    "intro_taranee_final": ("cutscenes/intro/processed/taranee_final.png", "actor"),
    "intro_cornelia_t1": ("cutscenes/intro/processed/cornelia_t1.png", "actor"),
    "intro_cornelia_t2": ("cutscenes/intro/processed/cornelia_t2.png", "actor"),
    "intro_cornelia_final": ("cutscenes/intro/processed/cornelia_final.png", "actor"),
    "intro_haylin_t1": ("cutscenes/intro/processed/haylin_t1.png", "actor"),
    "intro_haylin_t2": ("cutscenes/intro/processed/haylin_t2.png", "actor"),
    "intro_haylin_final": ("cutscenes/intro/processed/haylin_final.png", "actor"),
    "intro_caleb_t1": ("cutscenes/intro/processed/caleb_t1.png", "actor"),
    "intro_caleb_t2": ("cutscenes/intro/processed/caleb_t2.png", "actor"),
    "intro_caleb_final": ("cutscenes/intro/processed/caleb_final.png", "actor"),
    "intro_blunk_t1": ("cutscenes/intro/processed/blunk_t1.png", "actor"),
    "intro_blunk_t2": ("cutscenes/intro/processed/blunk_t2.png", "actor"),
    "intro_blunk_final": ("cutscenes/intro/processed/blunk_final.png", "actor"),
    "intro_irma_horror": ("cutscenes/intro/processed/irma_horror.png", "actor"),

    # 100 line cutscene
    "l100_phobos": ("cutscenes/lines100/phobos_action.png", "actor"),
    "l100_will": ("cutscenes/lines100/will_action.png", "actor"),
    "l100_irma": ("cutscenes/intro/processed/irma_final.png", "actor"),
    "l100_taranee": ("cutscenes/lines100/taranee_action.png", "actor"),
    "l100_cornelia": ("cutscenes/lines100/cornelia_action.png", "actor"),
    "l100_haylin": ("cutscenes/lines100/haylin_action.png", "actor"),
    "l100_caleb": ("cutscenes/lines100/caleb_action.png", "actor"),
    "l100_heart": ("cutscenes/lines100/will_heart.png", "actor"),

    # 200 line cutscene / ending
    "l200_sheet_phobos": ("cutscenes/lines200/phobos_action_sheet.png", "fit"),
    "l200_sheet_heart": ("cutscenes/lines200/will_heart_sheet.png", "fit"),
    "ending_phobos": ("cutscenes/ending/art_phobos.jpg", "cover"),
    "ending_witch": ("cutscenes/ending/art_witch.jpg", "cover"),

    # Phobos room / menu
    "phobos_menu_body": ("menu/phobos/menu_body_opaque.png", "actor"),
    "phobos_gameplay": ("menu/phobos/menu_body_opaque.png", "actor"),
    "phobos_resistance": ("cutscenes/lines100/phobos_action.png", "actor"),
    "phobos_room_bg": ("cutscenes/phobos_room/background_v2.png", "cover"),
    "phobos_room_table": ("cutscenes/phobos_room/table_foreground.png", "fit"),

}

CORE_AUDIO = {
    "menu_1.mp3": "audio/music/menu/menu_1.mp3",
    "menu_2.mp3": "audio/music/menu/menu_2.mp3",
    "intro.mp3": "audio/collection/intro_music.mp3",
    "phase0.mp3": "audio/music/phase_0_99_phobos/Arrogant_Prince_of_the_Obsidian_Court.mp3",
    "phase1_1.mp3": "audio/music/phase_100_199_resistance/phase2_1.mp3",
    "phase1_2.mp3": "audio/music/phase_100_199_resistance/phase2_2.mp3",
    "phase1_3.mp3": "audio/music/phase_100_199_resistance/phase2_3.mp3",
    "phase2_guardians.mp3": "audio/collection/witch_ending.mp3",
    "phase2_phobos.mp3": "audio/music/phobos_route/Phobos_main_theme_3_phase.mp3",
    "phobos_room.mp3": "audio/music/phobos_room/PhobosthemeDark.mp3",
    "vtd_1.mp3": "audio/music/secrets/vtd/vtd_01.mp3",
    "vtd_2.mp3": "audio/music/secrets/vtd/vtd_02.mp3",
    "voice_phobos.mp3": "audio/voice/phobos/dark_side.mp3",
    "voice_matrix.mp3": "audio/voice/phobos/matrix_fan.mp3",
    "voice_porn.mp3": "audio/voice/phobos/porn_reaction.mp3",
    "voice_devq.mp3": "audio/voice/phobos/not_bad.mp3",
    "ending_outro.mp3": "audio/music/ending/witch_end_outro.mp3",
}

IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".m4a"}

def run(*args: str) -> None:
    subprocess.run(args, check=True)

def save_processed(src: Path, dst: Path, mode: str) -> None:
    with Image.open(src) as im:
        im = im.convert("RGBA")
        if mode == "cover":
            im = ImageOps.fit(im, (400, 240), method=Image.Resampling.LANCZOS)
        elif mode == "icon":
            im.thumbnail((96, 96), Image.Resampling.LANCZOS)
        elif mode == "actor":
            im.thumbnail((300, 220), Image.Resampling.LANCZOS)
        else:
            im.thumbnail((400, 240), Image.Resampling.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst)

def to_t3x(src_png: Path, out_t3x: Path, fmt: str = "auto-etc1") -> None:
    t3s = src_png.with_suffix(".t3s")
    t3s.write_text(f"--atlas -f {fmt} -z auto\n{src_png.name}\n", encoding="utf-8")
    out_t3x.parent.mkdir(parents=True, exist_ok=True)
    run("tex3ds", "-i", str(t3s), "-o", str(out_t3x))

def rotate_shape(shape):
    h = max(y for _, y in shape) + 1
    out = [(h - 1 - y, x) for x, y in shape]
    min_x = min(x for x, _ in out)
    min_y = min(y for _, y in out)
    return tuple((x - min_x, y - min_y) for x, y in out)

def build_phase1_cells() -> None:
    cells_dir = WORK / "phase1_cells"
    cells_dir.mkdir(parents=True, exist_ok=True)
    atlas_lines = ["--atlas -f rgba5551 -z auto"]
    for kind in KIND_ORDER:
        shape = BASE[kind]
        for rot in range(4):
            angle = rot * 90
            src = ASSETS / "sprites" / "phase1" / f"{kind}_rotation_{angle}.png"
            if not src.exists():
                raise FileNotFoundError(src)
            with Image.open(src) as im:
                im = im.convert("RGBA")
                for slot, (x, y) in enumerate(shape):
                    crop = im.crop((x * 24, y * 24, x * 24 + 24, y * 24 + 24))
                    name = f"cell_{kind}_{rot}_{slot}.png"
                    crop.save(cells_dir / name)
                    atlas_lines.append(name)
            shape = rotate_shape(shape)
    t3s = cells_dir / "phase1_cells.t3s"
    t3s.write_text("\n".join(atlas_lines) + "\n", encoding="utf-8")
    run("tex3ds", "-i", str(t3s), "-o", str(GFX / "phase1_cells.t3x"))


def remove_border_light(im: Image.Image, threshold: int = 238) -> Image.Image:
    """Pillow equivalent of main.py's make_border_light_transparent()."""
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    if w <= 0 or h <= 0:
        return im

    def is_bg(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        return a > 0 and min(r, g, b) >= threshold and max(r, g, b) - min(r, g, b) <= 18

    stack = []
    for x in range(w):
        stack.append((x, 0)); stack.append((x, h - 1))
    for y in range(h):
        stack.append((0, y)); stack.append((w - 1, y))

    background = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in background or x < 0 or y < 0 or x >= w or y >= h:
            continue
        if not is_bg(x, y):
            continue
        background.add((x, y))
        stack.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))

    for x, y in background:
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, 0)

    edge = set()
    for x, y in background:
        for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in background:
                edge.add((nx, ny))
    for x, y in edge:
        r, g, b, a = px[x, y]
        lo, hi = min(r, g, b), max(r, g, b)
        if lo >= 180 and hi - lo <= 30:
            alpha = max(0, min(255, int((238 - lo) * 255 / 58)))
            px[x, y] = (r, g, b, min(a, alpha))
    return im

def build_phobos_room_poses() -> None:
    room_dir = ASSETS / "cutscenes" / "phobos_room"
    sheet_path = room_dir / "phobos_seated_poses.png"
    if not sheet_path.exists():
        print(f"[3ds assets] seated Phobos sheet missing: {sheet_path}", file=sys.stderr)
        return

    with Image.open(sheet_path) as sheet:
        sheet = sheet.convert("RGBA")
        cell_w, cell_h = sheet.width // 3, sheet.height // 2
        pose_dir = WORK / "phobos_room_poses"
        pose_dir.mkdir(parents=True, exist_ok=True)

        pose_index = 0
        for row in range(2):
            for col in range(3):
                pose = sheet.crop((
                    col * cell_w, row * cell_h,
                    (col + 1) * cell_w, (row + 1) * cell_h
                ))
                pose = remove_border_light(pose)
                alpha = pose.getchannel("A")
                bbox = alpha.getbbox()
                if bbox:
                    pose = pose.crop(bbox)
                pose.thumbnail((250, 205), Image.Resampling.LANCZOS)
                out = pose_dir / f"phobos_room_pose{pose_index}.png"
                pose.save(out)
                to_t3x(out, GFX / f"phobos_room_pose{pose_index}.t3x", "rgba5551")
                pose_index += 1

    # The desktop v6.37.1 scene does NOT place table_foreground.png over the
    # character. background_v2 already contains the final desk/window geometry;
    # after drawing Phobos it simply repaints the lower part of that same
    # composite from y=700 on a 1080px canvas. Build the identical foreground
    # mask at 400x240 so the desk can never drift or scale differently on 3DS.
    bg_path = room_dir / "background_v2.png"
    if bg_path.exists():
        with Image.open(bg_path) as bg:
            bg = ImageOps.fit(bg.convert("RGBA"), (400, 240),
                              method=Image.Resampling.LANCZOS)
            table_top = int(round(240 * 700 / 1080))
            foreground = Image.new("RGBA", bg.size, (0, 0, 0, 0))
            foreground.alpha_composite(
                bg.crop((0, table_top, bg.width, bg.height)),
                (0, table_top)
            )
            out = WORK / "core" / "phobos_room_foreground.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            foreground.save(out)
            to_t3x(out, GFX / "phobos_room_foreground.t3x", "rgba5551")

def build_story_frames() -> None:
    # Six ready-made Phobos collapse frames are small enough to keep resident.
    for i in range(6):
        key = f"l200_collapse_{i}"
        src = ASSETS / "cutscenes" / "lines200" / "phobos_collapse_frames" / f"frame_0{i}.png"
        tmp = WORK / "core" / f"{key}.png"
        save_processed(src, tmp, "fit")
        to_t3x(tmp, GFX / f"{key}.t3x")


def build_sequence_atlas(key: str, files: list[Path], max_h: int = 150) -> None:
    seq_dir = WORK / "ending" / key
    seq_dir.mkdir(parents=True, exist_ok=True)
    atlas_lines = ["--atlas -f rgba5551 -z auto"]
    for index, src in enumerate(files):
        with Image.open(src) as im:
            im = im.convert("RGBA")
            im.thumbnail((190, max_h), Image.Resampling.LANCZOS)
            name = f"{index:02d}.png"
            im.save(seq_dir / name)
            atlas_lines.append(name)
    t3s = seq_dir / f"{key}.t3s"
    t3s.write_text("\n".join(atlas_lines) + "\n", encoding="utf-8")
    run("tex3ds", "-i", str(t3s), "-o", str(GFX / f"{key}.t3x"))

def build_ending_assets() -> None:
    ready = ASSETS / "cutscenes" / "ending" / "ready"
    picks = {
        "ending_heart": list(range(24)),
        "ending_will": [0,1,2,3,4,5],
        "ending_irma": [0,1,2,3,4,5],
        "ending_taranee": [0,1,2,3,4,5],
        "ending_haylin": [0,1,2,3,4,5],
        "ending_blunk": [0,1,2,3,4,5],
        "ending_caleb": [0,1,2,3,4,5],
        "ending_cornelia": [0,1,2,3,4,5],
        "ending_enemies": [0,1,2,3,4,5],
        "ending_bats": [0,1,2,3,4,5],
    }
    for key, indices in picks.items():
        stem = key.removeprefix("ending_")
        files = [ready / f"{stem}_{i:02d}.png" for i in indices]
        if all(p.exists() for p in files):
            build_sequence_atlas(key, files, 150 if stem != "blunk" else 105)

    cedric = ready / "cedric_00.png"
    if cedric.exists():
        build_sequence_atlas("ending_cedric", [cedric], 180)

def build_core() -> None:
    for p in (ROMFS, WORK, GFX, AUDIO):
        p.mkdir(parents=True, exist_ok=True)

    build_phase1_cells()
    build_phobos_room_poses()
    build_story_frames()
    build_ending_assets()

    for key, (rel, mode) in CORE_IMAGES.items():
        src = ASSETS / rel
        if not src.exists():
            print(f"[3ds assets] optional image missing: {src}", file=sys.stderr)
            continue
        tmp = WORK / "core" / f"{key}.png"
        save_processed(src, tmp, mode)
        to_t3x(tmp, GFX / f"{key}.t3x")

    for out_name, rel in CORE_AUDIO.items():
        src = ASSETS / rel
        if not src.exists():
            print(f"[3ds assets] optional audio missing: {src}", file=sys.stderr)
            continue
        shutil.copy2(src, AUDIO / out_name)

def safe_name(rel: Path) -> str:
    raw = rel.as_posix()
    stem = "".join(c if c.isalnum() else "_" for c in raw).strip("_")
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    return (stem[:96] + "_" + digest).lower()

def build_full() -> None:
    full_gfx = ROMFS / "full" / "gfx"
    full_audio = ROMFS / "full" / "audio"
    manifest = []
    for src in ASSETS.rglob("*"):
        if not src.is_file() or src.name.startswith("."):
            continue
        rel = src.relative_to(ASSETS)
        ext = src.suffix.lower()
        if ext in IMAGE_EXTS:
            key = safe_name(rel)
            tmp = WORK / "full" / f"{key}.png"
            try:
                save_processed(src, tmp, "fit")
                to_t3x(tmp, full_gfx / f"{key}.t3x")
                manifest.append(f"IMAGE\t{rel.as_posix()}\tromfs:/full/gfx/{key}.t3x")
            except Exception as exc:
                print(f"[3ds assets] skipped image {rel}: {exc}", file=sys.stderr)
        elif ext in AUDIO_EXTS:
            out = full_audio / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
            manifest.append(f"AUDIO\t{rel.as_posix()}\tromfs:/full/audio/{rel.as_posix()}")
    (ROMFS / "full" / "manifest.tsv").write_text("\n".join(manifest) + "\n", encoding="utf-8")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=("core", "full"), default="core")
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()

    if args.clean:
        shutil.rmtree(ROMFS, ignore_errors=True)
        shutil.rmtree(WORK, ignore_errors=True)

    shutil.rmtree(ROMFS, ignore_errors=True)
    shutil.rmtree(WORK, ignore_errors=True)
    build_core()
    if args.profile == "full":
        build_full()

    print(f"[3ds assets] prepared {args.profile} RomFS at {ROMFS}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
