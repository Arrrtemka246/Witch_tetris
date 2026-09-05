from __future__ import annotations

import json
import math
import random
import sys
import webbrowser
from pathlib import Path

import pygame

# ============================================================
# W.I.T.C.H. Tetris — Pygame build v6.37.1
# Full-color 50x50 source cells, auto-fit, transparency, Hold, story checkpoints and secret-code system.
# ============================================================

FPS = 60
BUILD_VERSION = "6.37.1"
BOARD_W = 10
BOARD_H = 20
CELL = 50
BOARD_X = 30
BOARD_Y = 30
HUD_W = 300
WINDOW_W = BOARD_X * 2 + BOARD_W * CELL + HUD_W
WINDOW_H = BOARD_Y * 2 + BOARD_H * CELL

# The game is always rendered internally at true 50x50-cell resolution.
# Only the final frame is nearest-neighbour scaled to fit the physical display.
DISPLAY_MARGIN = 80
MIN_DISPLAY_SCALE = 0.45

LINES_RESISTANCE = 100
LINES_PHASE2 = 200
SOFT_DROP_FRAMES = 2

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"
SPRITE_DIR = ASSET_DIR / "sprites" / "phase1"
PHASE2_SPRITE_DIR = ASSET_DIR / "sprites" / "phase2" / "lurdens"
HORROR_SPRITE_DIR = ASSET_DIR / "sprites" / "horror"
BACKGROUND_DIR = ASSET_DIR / "backgrounds"
MENU_DIR = ASSET_DIR / "menu"
PHOBOS_MENU_DIR = MENU_DIR / "phobos"
PHOBOS_FACE_DIR = PHOBOS_MENU_DIR / "faces"
MUSIC_ROOT = ASSET_DIR / "audio" / "music"
PHASE_MUSIC = {
    -1: MUSIC_ROOT / "menu",
    0: MUSIC_ROOT / "phase_0_99_phobos",
    1: MUSIC_ROOT / "phase_100_199_resistance",
    2: MUSIC_ROOT / "phase_200_plus_guardians",
    3: MUSIC_ROOT / "phobos_route",
}
PHASE_MUSIC_FALLBACKS = {
    # Until a separate Guardians soundtrack is supplied, the established
    # ending theme keeps the post-200 Guardians route from becoming silent.
    2: [ASSET_DIR / "audio" / "collection" / "witch_ending.mp3"],
}
RECORDS_PATH = BASE_DIR / "records.json"
SECRET_DIR = ASSET_DIR / "secrets"
PORN_DIR = SECRET_DIR / "porn"
JETIX_LOGO = SECRET_DIR / "jetix" / "Jetix.png"
VTD_DIR = MUSIC_ROOT / "secrets" / "vtd"
META_VIDEO_DIR = SECRET_DIR / "videos" / "prepared"
ADULT_SITES_FILE = SECRET_DIR / "videos" / "adult_sites_user_list.txt"
PHOBOS_ROOM_DIR = ASSET_DIR / "cutscenes" / "phobos_room"
SETTINGS_PATH = BASE_DIR / "settings.json"
SUPPORTED_IMAGES = {".png", ".jpg", ".jpeg", ".webp"}
EFFECT_DIR = ASSET_DIR / "effects"
SFX_DIR = ASSET_DIR / "audio" / "sfx"
LINES100_DIR = ASSET_DIR / "cutscenes" / "lines100"

# SDL scancodes are physical-key positions and therefore do not depend on
# the active macOS keyboard layout. This keeps WASD/W/X/Z/C working on both
# English and Russian layouts.
SC_A = 4
SC_C = 6
SC_D = 7
SC_S = 22
SC_W = 26
SC_X = 27
SC_Z = 29
SC_LSHIFT = 225
SC_RSHIFT = 229
SC_M = 16
SC_Q = 20
PHYSICAL_LETTERS = {4 + i: chr(ord("a") + i) for i in range(26)}
SUPPORTED_AUDIO = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
VOICE_DIR = ASSET_DIR / "audio" / "voice" / "phobos"

# The supplied action sheet is laid out as 4 + 5 + 5 poses rather than a
# regular 4x3 grid. Rectangles intentionally stop before neighbouring poses.
PHOBOS_ACTION_RECTS = [
    (0, 0, 384, 330), (384, 0, 384, 330), (768, 0, 384, 330), (1152, 0, 384, 330),
    (0, 330, 307, 332), (307, 330, 307, 332), (614, 330, 307, 332),
    (921, 330, 307, 332), (1228, 330, 308, 332),
    (0, 662, 307, 362), (307, 662, 307, 362), (614, 662, 307, 362),
    (921, 662, 307, 362), (1228, 662, 308, 362),
]

# Same geometry as the last Pyxel build.
BASE_SHAPES = {
    "I": [(0, 0), (0, 1), (0, 2), (0, 3)],
    "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "T": [(0, 0), (1, 0), (2, 0), (1, 1)],
    "S": [(0, 0), (1, 0), (1, 1), (2, 1)],
    "Z": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
    "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
}
PIECES = list(BASE_SHAPES)

COLORS = {
    "bg": (11, 11, 18),
    "board": (18, 20, 30),
    "grid": (42, 44, 58),
    "text": (235, 235, 245),
    "accent": (178, 108, 255),
    "danger": (220, 80, 95),
}

# Vanilla tetromino palette used by the Phobos 20% "ordinary pieces" branch.
# These blocks intentionally contain NO character artwork.
PLAIN_TETRIS_COLORS = PIECE_COLORS = {
    "I": (0, 210, 220),
    "J": (20, 25, 235),
    "L": (242, 158, 0),
    "O": (242, 238, 0),
    "S": (0, 225, 25),
    "T": (165, 0, 235),
    "Z": (238, 0, 0),
}


def rotate_shape(shape):
    max_y = max(y for _, y in shape)
    h = max_y + 1
    out = [(h - 1 - y, x) for x, y in shape]
    min_x = min(x for x, _ in out)
    min_y = min(y for _, y in out)
    return [(x - min_x, y - min_y) for x, y in out]


SHAPES = {}
for kind, base in BASE_SHAPES.items():
    rots = [base]
    for _ in range(3):
        rots.append(rotate_shape(rots[-1]))
    SHAPES[kind] = rots


def bbox(shape):
    return max(x for x, _ in shape) + 1, max(y for _, y in shape) + 1


def build_will_maze():
    """Return an original Pac-Man-like maze with one central wrap tunnel.

    Solid mirrored islands create readable lanes while leaving the whole map
    connected.  This is intentionally not a copy of the arcade maze.
    """
    width, height, tunnel_y = 28, 31, 15
    walls = {(x, 0) for x in range(width)} | {(x, height - 1) for x in range(width)}
    walls |= {(0, y) for y in range(height)} | {(width - 1, y) for y in range(height)}
    walls -= {(0, tunnel_y), (width - 1, tunnel_y)}

    def solid(left, top, right, bottom):
        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                walls.add((x, y))

    # Paired top/bottom islands give the board its maze rhythm without long
    # fence lines that look like a spreadsheet.
    top_islands = (
        (2, 2, 6, 4), (9, 2, 11, 4), (16, 2, 18, 4), (21, 2, 25, 4),
        (2, 7, 4, 9), (7, 7, 11, 9), (16, 7, 20, 9), (23, 7, 25, 9),
        (2, 12, 6, 13), (8, 11, 10, 13), (17, 11, 19, 13), (21, 12, 25, 13),
    )
    for rect in top_islands:
        solid(*rect)
        left, top, right, bottom = rect
        solid(left, height - 1 - bottom, right, height - 1 - top)

    # Central ghost house. The two top cells form the only door.
    for x in range(11, 17):
        walls.add((x, 13)); walls.add((x, 18))
    for y in range(13, 19):
        walls.add((11, y)); walls.add((16, y))
    walls -= {(13, 13), (14, 13)}
    return width, height, tunnel_y, walls


def will_maze_step(cell, direction, walls, width=28, height=31, tunnel_y=15):
    x, y = cell; dx, dy = direction
    nx, ny = x + dx, y + dy
    if y == tunnel_y and dy == 0 and nx < 0:
        nx = width - 1
    elif y == tunnel_y and dy == 0 and nx >= width:
        nx = 0
    if not (0 <= nx < width and 0 <= ny < height) or (nx, ny) in walls:
        return None
    return nx, ny


def heart_brick_layout(arena, wave=1):
    """Pixel rectangles for an always-reachable 11-column brick wave."""
    left, top, width, _height = arena
    columns = 11; gap = 7; margin = 30
    brick_w = (width - margin * 2 - gap * (columns - 1)) // columns
    rows = min(7, 4 + wave // 2)
    return [(left + margin + x * (brick_w + gap), top + 30 + y * 34, brick_w, 26)
            for y in range(rows) for x in range(columns)]


def taranee_invader_layout(arena, wave=1):
    """Ten evenly-spaced columns, all inside Taranee's firing lane."""
    left, top, width, _height = arena
    columns = 10; rows = min(6, 3 + (wave + 1) // 2); margin = 45
    step = (width - margin * 2) / (columns - 1)
    return [[left + margin + x * step, top + 45 + y * 48]
            for y in range(rows) for x in range(columns)]


def irma_dark_water_curve(tick):
    """Return the visible level, spawn interval and speed for Irma's five lanes."""
    level = 1 + max(0, tick) // (FPS * 18)
    return level, max(30, 86 - level * 4), 3.0 + min(5.0, (level - 1) * .32)


class MusicPool:
    def __init__(self):
        self.phase = None
        self.queue = []
        self.current = None
        self.enabled = True
        self.paused = False
        self.loop_current = False
        self.special_lock = False
        self.base_volume = 0.72
        self.duck_volume = 0.25
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.base_volume)

    @staticmethod
    def ready():
        return bool(pygame.mixer.get_init())

    def scan(self, folder: Path):
        if not folder.exists():
            return []
        return [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO]

    def set_phase(self, phase: int, force=False):
        if self.phase == phase and not force:
            return
        self.phase = phase
        self.paused = False
        self.queue.clear()
        self.current = None
        # A special soundtrack (VTD) owns the audio while locked. Remember the
        # new phase but never start normal music underneath it.
        if self.enabled and not self.special_lock and self.ready():
            pygame.mixer.music.stop()
            self.play_next()

    def refill(self):
        files = self.scan(PHASE_MUSIC[self.phase]) if self.phase in PHASE_MUSIC else []
        if not files:
            files = [p for p in PHASE_MUSIC_FALLBACKS.get(self.phase, []) if p.exists()]
        random.shuffle(files)
        if len(files) > 1 and self.current is not None and files and files[0] == self.current:
            files[0], files[1] = files[1], files[0]
        self.queue = files

    def play_next(self):
        if not self.enabled or self.phase is None or self.special_lock or not self.ready():
            return
        # Keep a shuffled bag; refill only after every track in this phase was used.
        if not self.queue:
            self.refill()
        if not self.queue:
            return
        self.current = self.queue.pop(0)
        try:
            pygame.mixer.music.load(str(self.current))
            pygame.mixer.music.play(-1 if self.loop_current else 0)
            pygame.mixer.music.set_volume(self.base_volume)
        except pygame.error as exc:
            print(f"[music] Could not play {self.current.name}: {exc}")
            self.current = None

    def skip(self):
        if self.enabled and self.phase is not None and not self.special_lock and self.ready():
            pygame.mixer.music.stop()
            self.play_next()

    def toggle_loop(self):
        self.loop_current = not self.loop_current
        if self.current and self.enabled and not self.special_lock and self.ready():
            try:
                pygame.mixer.music.load(str(self.current))
                pygame.mixer.music.play(-1 if self.loop_current else 0)
                pygame.mixer.music.set_volume(self.base_volume)
            except pygame.error:
                pass
        return self.loop_current

    def duck(self, on=True):
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.duck_volume if on else self.base_volume)

    def update(self):
        if self.ready() and self.enabled and not self.special_lock and not self.paused and self.phase is not None and not pygame.mixer.music.get_busy():
            self.play_next()

    def pause(self):
        if self.ready() and self.enabled and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True

    def resume(self):
        if self.special_lock:
            return
        if self.ready() and self.enabled and self.paused:
            pygame.mixer.music.unpause()
            self.paused = False

    def toggle(self):
        self.enabled = not self.enabled
        self.paused = False
        if not self.ready():
            return
        if self.enabled:
            if not self.special_lock:
                self.play_next()
        else:
            pygame.mixer.music.stop()

    def enter_special(self):
        self.special_lock = True
        self.paused = False
        # Stop instead of pause: this guarantees there is no hidden normal
        # stream that can resume underneath VTD after a phase/menu transition.
        if self.ready():
            pygame.mixer.music.stop()

    def leave_special(self, restart=True):
        self.special_lock = False
        self.paused = False
        if restart and self.enabled and self.phase is not None:
            self.queue.clear()
            self.current = None
            self.play_next()

    def stop(self):
        if self.ready():
            pygame.mixer.music.stop()


def make_border_black_transparent(surface: pygame.Surface, threshold: int = 30) -> pygame.Surface:
    """Remove only near-black pixels connected to the image border.

    This makes the black canvas around generated/source sprites transparent while
    preserving black outlines and dark details enclosed inside the character.
    """
    src = surface.convert_alpha().copy()
    w, h = src.get_size()
    if w == 0 or h == 0:
        return src

    def is_bg(x, y):
        c = src.get_at((x, y))
        return c.a > 0 and c.r <= threshold and c.g <= threshold and c.b <= threshold

    stack = []
    seen = set()
    for x in range(w):
        stack.append((x, 0)); stack.append((x, h - 1))
    for y in range(h):
        stack.append((0, y)); stack.append((w - 1, y))

    while stack:
        x, y = stack.pop()
        if (x, y) in seen or x < 0 or y < 0 or x >= w or y >= h:
            continue
        seen.add((x, y))
        if not is_bg(x, y):
            continue
        c = src.get_at((x, y))
        src.set_at((x, y), (c.r, c.g, c.b, 0))
        if x > 0: stack.append((x - 1, y))
        if x + 1 < w: stack.append((x + 1, y))
        if y > 0: stack.append((x, y - 1))
        if y + 1 < h: stack.append((x, y + 1))
    return src


def make_border_light_transparent(surface: pygame.Surface, threshold: int = 238) -> pygame.Surface:
    """Remove only the near-white canvas connected to a sprite's border.

    The six supplied seated Phobos poses use an opaque white sheet.  A border
    flood fill preserves his pale hair and hands, while a narrow feather pass
    removes the light fringe without touching the black costume.
    """
    src = surface.convert_alpha().copy()
    width, height = src.get_size()
    if width == 0 or height == 0:
        return src

    def is_background(x, y):
        color = src.get_at((x, y))
        return (
            color.a > 0
            and min(color.r, color.g, color.b) >= threshold
            and max(color.r, color.g, color.b) - min(color.r, color.g, color.b) <= 18
        )

    stack = []
    for x in range(width):
        stack.extend(((x, 0), (x, height - 1)))
    for y in range(height):
        stack.extend(((0, y), (width - 1, y)))
    background = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in background or not (0 <= x < width and 0 <= y < height):
            continue
        if not is_background(x, y):
            continue
        background.add((x, y))
        stack.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    for x, y in background:
        color = src.get_at((x, y))
        src.set_at((x, y), (color.r, color.g, color.b, 0))

    # Feather only pixels touching the removed exterior. Cream hair highlights
    # are chromatic enough to remain fully opaque.
    edge = set()
    for x, y in background:
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in background:
                edge.add((nx, ny))
    for x, y in edge:
        color = src.get_at((x, y))
        low, high = min(color.r, color.g, color.b), max(color.r, color.g, color.b)
        if low >= 180 and high - low <= 30:
            alpha = max(0, min(255, int((238 - low) * 255 / 58)))
            src.set_at((x, y), (color.r, color.g, color.b, min(color.a, alpha)))
    return src


def load_clean_alpha(path: Path, threshold: int = 30) -> pygame.Surface:
    """Load a sprite sheet crop and discard disconnected neighbour fragments.

    Several supplied PNG files were rectangular crops from larger sprite
    sheets.  Their black canvas is removed first; afterwards only the main
    connected silhouette (and substantial connected companions) are kept.
    This removes Will's stray hand, the top strips above Taranee/Hay Lin and
    the extra fragments around Caleb, Cornelia and Phobos without rewriting
    the source artwork.
    """
    # The old standalone Phobos action PNG had already lost the RGB values of
    # many dark pixels, so no alpha post-processing could reconstruct them.
    # Its opaque source sheet still contains the complete cloak. Rebuild that
    # pose in memory and remove only black pixels connected to the crop border;
    # internal black folds remain opaque.
    if path.name == "phobos_action.png" and path.parent.name == "lines100":
        source_sheet = path.parent.parent / "lines200" / "phobos_action_sheet.png"
        if source_sheet.exists():
            sheet = pygame.image.load(str(source_sheet)).convert_alpha()
            # This standalone frame is an exact 352x288 crop beginning at
            # (28, 28) in the supplied 4x4 sheet.
            crop = pygame.Rect(28, 28, min(352, sheet.get_width()-28), min(288, sheet.get_height()-28))
            src = sheet.subsurface(crop).copy()
            # The old PNG still has a useful outer silhouette even though its
            # black fabric pixels are transparent. Scale that silhouette to
            # the intact source and close only small internal gaps. This keeps
            # the empty space around his hands while restoring cloak folds.
            damaged = pygame.image.load(str(path)).convert_alpha()
            silhouette = pygame.mask.from_surface(damaged, 8).to_surface(
                setcolor=(255,255,255,255), unsetcolor=(0,0,0,0)
            )
            mask = pygame.mask.from_surface(silhouette, 8)
            mask = close_small_mask_gaps(mask, max_gap=36)
            matte = mask.to_surface(setcolor=(255,255,255,255), unsetcolor=(0,0,0,0))
            src.blit(matte, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
            return src
    src = pygame.image.load(str(path)).convert_alpha()
    return clean_alpha_surface(src, threshold)


def close_small_mask_gaps(mask: pygame.mask.Mask, max_gap: int = 36) -> pygame.mask.Mask:
    """Close short holes in a sprite silhouette without filling limb gaps."""
    out = mask.copy(); width,height = out.get_size()
    for y in range(height):
        filled=[x for x in range(width) if out.get_at((x,y))]
        for left,right in zip(filled,filled[1:]):
            if 1 < right-left <= max_gap+1:
                for x in range(left+1,right): out.set_at((x,y),1)
    for x in range(width):
        filled=[y for y in range(height) if out.get_at((x,y))]
        for top,bottom in zip(filled,filled[1:]):
            if 1 < bottom-top <= max_gap+1:
                for y in range(top+1,bottom): out.set_at((x,y),1)
    return out


def clean_alpha_surface(src: pygame.Surface, threshold: int = 30) -> pygame.Surface:
    """Surface variant used for in-memory sprite-sheet frames."""
    # Files with an existing transparent background must not be black-keyed:
    # doing so ate the dark links between parts of Phobos's cloak and left his
    # hands floating as separate islands. Black-key only almost-opaque legacy
    # crops; otherwise trust the supplied alpha channel.
    raw_mask = pygame.mask.from_surface(src, 8)
    if raw_mask.count() >= src.get_width() * src.get_height() * 0.98:
        src = make_border_black_transparent(src, threshold=threshold)
    else:
        src = src.convert_alpha().copy()
    try:
        components = pygame.mask.from_surface(src, 8).connected_components(4)
    except (AttributeError, pygame.error):
        return src
    if not components:
        return src
    components.sort(key=lambda mask: mask.count(), reverse=True)
    largest = max(1, components[0].count())
    keep = pygame.mask.Mask(src.get_size(), fill=False)
    # Detached anti-aliasing specks and neighbouring sheet cells are small;
    # legitimate secondary parts are retained when they are substantial.
    for component in components:
        if component.count() >= largest * 0.12:
            keep.draw(component, (0, 0))
    matte = keep.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
    cleaned = src.copy()
    cleaned.blit(matte, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return cleaned


class SpriteSet:
    """Loads phase-1 sprites and optional 200+ Lurden replacements.

    If phase2/lurdens is still empty, phase 2 intentionally falls back to
    phase-1 art, so the game is playable now and the seven models can be
    dropped in later without changing gameplay code.
    """

    def __init__(self):
        self.phase_sets = {0: self._load_folder(SPRITE_DIR)}
        # Phase 1 resistance keeps the transformed-hero set.
        self.phase_sets[1] = self.phase_sets[0]
        p2 = self._load_folder(PHASE2_SPRITE_DIR, allow_missing=True)
        self.phase_sets[2] = p2 if any(p2["pieces"][k][0] is not None for k in PIECES) else self.phase_sets[0]
        self.horror_set = self._load_folder(HORROR_SPRITE_DIR, allow_missing=True)

    def _load_folder(self, folder: Path, allow_missing=False):
        pieces, cells = {}, {}
        preprocessed = (folder / ".alpha_preprocessed").exists()
        for kind in PIECES:
            pieces[kind], cells[kind] = [], []
            for r in range(4):
                path = folder / f"{kind}_rotation_{r * 90}.png"
                if not path.exists():
                    pieces[kind].append(None); cells[kind].append({}); continue
                img = pygame.image.load(str(path)).convert_alpha()
                if not preprocessed:
                    img = make_border_black_transparent(img)
                w_cells, h_cells = bbox(SHAPES[kind][r])
                full = pygame.transform.scale(img, (w_cells * CELL, h_cells * CELL))
                pieces[kind].append(full)
                cellmap = {}
                for x, y in SHAPES[kind][r]:
                    rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
                    cellmap[(x, y)] = full.subsurface(rect).copy()
                cells[kind].append(cellmap)
        return {"pieces": pieces, "cells": cells}

    def _set(self, phase, horror=False):
        if horror and any(self.horror_set["pieces"][k][0] is not None for k in PIECES):
            return self.horror_set
        return self.phase_sets.get(phase, self.phase_sets[0])

    def draw_piece(self, screen, kind, rotation, gx, gy, phase=0, horror=False):
        data = self._set(phase, horror)
        img = data["pieces"][kind][rotation]
        if img is not None:
            screen.blit(img, (BOARD_X + gx * CELL, BOARD_Y + gy * CELL))
        else:
            # Per-kind fallback if a future Lurden pack is only partly filled.
            fallback = self.phase_sets[0]["pieces"][kind][rotation]
            if fallback is not None:
                screen.blit(fallback, (BOARD_X + gx * CELL, BOARD_Y + gy * CELL))
            else:
                for x, y in SHAPES[kind][rotation]:
                    pygame.draw.rect(screen, COLORS["accent"], (BOARD_X + (gx+x)*CELL, BOARD_Y + (gy+y)*CELL, CELL, CELL))

    def cell_surface(self, kind, rotation, local_xy, phase=0, horror=False):
        data = self._set(phase, horror)
        surf = data["cells"][kind][rotation].get(local_xy)
        if surf is None:
            surf = self.phase_sets[0]["cells"][kind][rotation].get(local_xy)
        return surf

    def piece_image(self, kind, rotation=0, phase=0, horror=False):
        data = self._set(phase, horror)
        img = data["pieces"][kind][rotation]
        return img if img is not None else self.phase_sets[0]["pieces"][kind][rotation]


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error as exc:
            print(f"[audio] pygame.mixer unavailable: {exc}")
        pygame.display.set_caption(f"W.I.T.C.H. Tetris — Pygame v{BUILD_VERSION}")
        info = pygame.display.Info()
        avail_w = max(640, info.current_w - DISPLAY_MARGIN)
        avail_h = max(520, info.current_h - DISPLAY_MARGIN)
        self.display_scale = min(1.0, avail_w / WINDOW_W, avail_h / WINDOW_H)
        self.display_scale = max(MIN_DISPLAY_SCALE, self.display_scale)
        self.display_size = (max(1, int(WINDOW_W * self.display_scale)), max(1, int(WINDOW_H * self.display_scale)))
        self.window = pygame.display.set_mode(self.display_size, pygame.RESIZABLE)
        self.canvas = pygame.Surface((WINDOW_W, WINDOW_H)).convert()
        self.fullscreen = False
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 28)
        self.small = pygame.font.SysFont("Arial", 21)
        self.big = pygame.font.SysFont("Arial", 54, bold=True)
        # v6.14: gameplay sprites are loaded lazily only when NEW GAME is selected.
        # This removes the expensive 28-sprite preprocessing from application startup.
        self.sprites = None
        self.music = MusicPool()
        self.running = True
        # Session-wide story result: once Phobos has been defeated at 200+,
        # his defeat-only taunts stay disabled until the app is restarted.
        self.session_has_victory = False
        self.consecutive_game_overs = 0
        self.loser_streak_voice_used = False

        # v6.14: opening cutscene v2. Assets are preprocessed at build time,
        # so startup only performs fast PNG loads (no per-pixel alpha cleanup).
        self.mode = "intro"
        self.menu_items = ["NEW GAME", "RECORDS", "SETTINGS", "COLLECTION", "QUIT"]
        self.menu_index = 0
        self.menu_tick = 0
        # v6.30 test collection: intentionally everything is unlocked.
        self.collection_sections = ["CUTSCENES", "ART & SPRITES", "AUDIO", "MINIGAMES", "DEVELOPMENT ARCHIVE", "BACK"]
        self.collection_index = 0
        self.collection_page = "root"
        self.collection_item_index = 0
        self.collection_items = []
        self.minigame_names = ["SNAKE — BLUNK/CEDRIC/PHOBOS", "WILL MAZE", "HAY LIN FLIGHT", "CALEB RUNNER", "HEART BREAKER", "TARANEE FIRE SHOT", "CORNELIA EARTH GARDEN", "BLUNK WASHING", "IRMA BUBBLE TROUBLE", "IRMA WHIRLPOOL", "BLUNK TREASURE ESCAPE", "CORNELIA STONE COVERS", "IRMA DARK WATER PANIC", "PHOBOS TETRIS ???"]
        self.minigame_index = 0
        self.minigame = None
        self.collection_cutscene = False
        self.collection_audio_item = None
        self.collection_gallery_files = []
        self.collection_gallery_title = ""
        self.collection_gallery_parent = "ART & SPRITES"
        self.mg_score = 0
        self.mg_tick = 0
        self.mg_player = [450, 760]
        self.mg_objects = []
        self.mg_dir = (1,0)
        self.mg_snake = [(10,10),(9,10),(8,10)]
        self.mg_food = (16,10)
        self.splash_tick = 0
        self.intro_tick = 0
        self.intro_scene = 0
        self.intro_scene_tick = 0
        self.intro_music_stage = None
        self.intro_music_path = None
        self.intro_dir = ASSET_DIR / "cutscenes" / "intro"
        self.intro_processed_dir = self.intro_dir / "processed"
        self.intro_images = {}
        intro_files = {
            "castle":"castle_exterior.png", "hall":"throne_hall.png",
            "phobos_normal":"processed/phobos_normal.png", "phobos_cast":"processed/phobos_cast.png",
            "will_normal":"processed/will_normal.png", "irma_normal":"processed/irma_normal.png",
            "taranee_normal":"processed/taranee_normal.png", "cornelia_normal":"processed/cornelia_normal.png",
            "haylin_normal":"processed/haylin_normal.png", "caleb_normal":"processed/caleb_normal.png",
            "blunk_normal":"processed/blunk_normal.png",
            "will_t1":"processed/will_t1.png", "will_t2":"processed/will_t2.png",
            "irma_t1":"processed/irma_t1.png", "irma_t2":"processed/irma_t2.png",
            "irma_horror":"processed/irma_horror.png",
            "taranee_t1":"processed/taranee_t1.png", "taranee_t2":"processed/taranee_t2.png",
            "cornelia_t1":"processed/cornelia_t1.png", "cornelia_t2":"processed/cornelia_t2.png",
            "haylin_t1":"processed/haylin_t1.png", "haylin_t2":"processed/haylin_t2.png",
            "caleb_t1":"processed/caleb_t1.png", "caleb_t2":"processed/caleb_t2.png",
            "blunk_t1":"processed/blunk_t1.png", "blunk_t2":"processed/blunk_t2.png",
            "will_final":"processed/will_final.png", "irma_final":"processed/irma_final.png",
            "taranee_final":"processed/taranee_final.png", "cornelia_final":"processed/cornelia_final.png",
            "haylin_final":"processed/haylin_final.png", "caleb_final":"processed/caleb_final.png",
            "blunk_final":"processed/blunk_final.png",
        }
        for key, rel in intro_files.items():
            fp = self.intro_dir / rel
            if fp.exists():
                try:
                    im = pygame.image.load(str(fp))
                    self.intro_images[key] = im.convert() if key in ("castle","hall") else im.convert_alpha()
                except pygame.error as exc:
                    print(f"[intro] Could not load {fp.name}: {exc}")

        self.intro_characters = ("will", "irma", "cornelia", "taranee", "haylin", "caleb", "blunk")
        self.intro_names = {"will":"ВИЛЛ", "irma":"ИРМА", "cornelia":"КОРНЕЛИЯ", "taranee":"ТАРАНИ",
                            "haylin":"ХАЙ ЛИН", "caleb":"КАЛЕБ", "blunk":"БЛАНК"}
        self.intro_opening_lines = {
            "irma":["Может, сразу сдашься? У нас вообще-то были планы на вечер.",
                    "Можешь перестать улыбаться. Ты проиграл.",
                    "Не терпится начистить тебе рожу!"],
            "cornelia":["Сдавайся. Мне совсем не хочется пачкать об тебя руки.",
                        "Давай без глупостей. Я не собираюсь пачкать руки."],
            "taranee":["Не пытайся ничего сделать. Мы готовы.",
                       "Лучше сдавайся, Фобос. Мы готовы к любой твоей уловке."],
            "haylin":["Ха-ха! Не верится, что мы наконец-то победили!",
                      "Ура! Кажется, на этот раз мы действительно победили!"],
            "caleb":["Твоё правление закончено, Фобос.",
                     "Наконец над Меридианом вновь засияет свет."],
            "blunk":["Ха! Фобос теперь попался!", "Ха! Бланк победит!"]
        }
        self.intro_transform_lines = {
            "will":["Что происходит?!", "Стражницы! Держитесь!"],
            "irma":["Эй! У меня всегда были другие представления о хорошей фигуре!",
                    "Эй! Что ты сделал?!"],
            "cornelia":["Только не говори, что это мой новый вид!",
                        "Что ты с нами делаешь?!"],
            "taranee":["Я не могу двигаться! Что это за заклинание?!",
                       "Это заклинание... оно меняет наши тела!"],
            "haylin":["Девочки... что-то не так!", "Эй! Я не могу остановиться!"],
            "caleb":["Фобос!", "Что ты сделал?!"],
            "blunk":["Бланку это совсем не нравится!", "А-А-А! БЛАНК!!!"]
        }
        # Will always opens the confrontation. A second speaker is random.
        self.intro_second_character = random.choice(tuple(self.intro_opening_lines))
        self.intro_second_line = random.choice(self.intro_opening_lines[self.intro_second_character])
        self.intro_phobos_line = random.choice(("Кончено?! Ха! Всё только начинается!",
                                                "Кончено?! Вы ещё ничего не видели!"))
        # Transformation: 50% mass shot, 50% one random character.
        self.intro_transform_all = (random.random() < 0.50)
        self.intro_transform_character = random.choice(self.intro_characters)
        self.intro_horror_irma = (random.randrange(10) == 0)
        self.intro_transform_line = random.choice(self.intro_transform_lines[self.intro_transform_character])
        self.intro_voice_channel = pygame.mixer.Channel(3) if pygame.mixer.get_init() else None
        self.intro_voice_played = False
        self.intro_final_voice_label = ""
        # v6.15 cutscene controls / SFX. Dialogue is player-paced with SPACE.
        self.intro_scene_sfx_played = set()
        self.intro_text_last_blip_char = -1
        self.intro_sfx_channel = pygame.mixer.Channel(4) if pygame.mixer.get_init() else None
        self.intro_text_channel = pygame.mixer.Channel(5) if pygame.mixer.get_init() else None
        self.intro_sfx = {}
        if pygame.mixer.get_init():
            intro_sfx_dir = SFX_DIR / "intro"
            for _name, _file in {
                "lightning":"lightning.wav", "ominous":"ominous_hit.wav",
                "drone":"transform_drone.wav", "text":"text_blip.wav",
                "magic1":"new_magic_1.wav", "magic2":"new_magic_2.wav",
            }.items():
                _p = intro_sfx_dir / _file
                if _p.exists():
                    try: self.intro_sfx[_name] = pygame.mixer.Sound(str(_p))
                    except pygame.error: pass
        final_voice_candidates = [
            (VOICE_DIR / "extra2" / "your_power_is_nothing.wav", "Теперь ваша сила против моей — ничто.", 20),
            (VOICE_DIR / "extra2" / "new_era_phobos.wav", "Начинается новая эра — эра Фобоса.", 16),
            (VOICE_DIR / "dark_side.mp3", "Ты познаешь всю мощь тёмной стороны.", 16),
            (VOICE_DIR / "extra" / "brilliant_laugh.wav", "Ха-ха-ха!", 14),
            (VOICE_DIR / "extra" / "lets_begin.wav", "Ну что же. Начнём.", 12),
            (VOICE_DIR / "meridian_mine.mp3", "Меридиан принадлежит мне.", 10),
            (VOICE_DIR / "extra2" / "haha_no_way.wav", "Ха! Не выйдет.", 12),
        ]
        final_voice_candidates = [(p,l,w) for p,l,w in final_voice_candidates if p.exists()]
        if final_voice_candidates:
            chosen = random.choices(final_voice_candidates, weights=[x[2] for x in final_voice_candidates], k=1)[0]
            self.intro_final_voice_path, self.intro_final_voice_label = chosen[0], chosen[1]
        else:
            self.intro_final_voice_path = None

        # v6.17: 100-line fourth-wall cutscene. Heavy assets are lazy-loaded
        # only when the checkpoint is actually reached.
        self.story100_assets = {}
        self.story100_loaded = False
        self.story100_tick = 0
        self.story100_stage = "idle"
        self.story100_variant = "plain"
        self.story100_jokes = []
        self.story100_seed = 0
        self.story100_speaker = "will"
        self.story100_speaker_line = "Заклинание слабеет!"
        self.story100_sfx_played = set()
        self.story100_masks = {}
        self.story100_silhouette_cache = {}
        self.story100_channel = pygame.mixer.Channel(6) if pygame.mixer.get_init() else None
        self.story100_mono = pygame.font.SysFont("Menlo", 15)
        self.story100_small_mono = pygame.font.SysFont("Menlo", 12)

        self.backgrounds = {}
        for key, name in {
            0: "phase_0_99_throne.png",
            1: "phase_100_199_unstable.png",
            2: "phase_200_plus_liberated.png",
            "menu": "menu_palace_exterior.png",
        }.items():
            path = BACKGROUND_DIR / name
            if path.exists():
                try:
                    self.backgrounds[key] = pygame.image.load(str(path)).convert()
                except pygame.error:
                    pass
        self.phobos_body = None
        body_path = PHOBOS_MENU_DIR / "menu_body_opaque.png"
        if not body_path.exists():
            body_path = PHOBOS_MENU_DIR / "menu_body.png"
        if body_path.exists():
            try:
                loaded_body = pygame.image.load(str(body_path)).convert_alpha()
                self.phobos_body = loaded_body if body_path.name == "menu_body_opaque.png" else make_border_black_transparent(loaded_body, threshold=1)
            except pygame.error:
                pass
        self.phobos_resistance_body = None
        # resistance_body.png contains large transparent holes where black
        # costume pixels were destructively keyed out in an earlier build.
        # Use the intact opaque action sheet through load_clean_alpha instead.
        repaired_action = LINES100_DIR / "phobos_action.png"
        resistance_path = PHOBOS_MENU_DIR / "resistance_body.png"
        try:
            if repaired_action.exists():
                self.phobos_resistance_body = load_clean_alpha(repaired_action)
            elif resistance_path.exists():
                self.phobos_resistance_body = load_clean_alpha(resistance_path)
        except pygame.error:
            self.phobos_resistance_body = None

        self.vtd_observer = None
        vtd_observer_path = MENU_DIR / "vtd" / "observer.jpg"
        if vtd_observer_path.exists():
            try:
                self.vtd_observer = make_border_black_transparent(
                    pygame.image.load(str(vtd_observer_path)).convert_alpha(), threshold=12
                )
            except pygame.error:
                pass
        self.phobos_faces = {}
        for name in ("neutral", "blink", "half_blink", "talk_a", "talk_b", "angry_talk", "smirk", "surprise", "furious", "suspicious"):
            fp = PHOBOS_FACE_DIR / f"{name}.png"
            if fp.exists():
                try:
                    self.phobos_faces[name] = load_clean_alpha(fp)
                except pygame.error:
                    pass

        # Secret/easter-egg state. Codes are read from event.unicode, so EN/RU layouts differ naturally.
        self.secret_codes = {
            "porn": "porn_gallery",
            "порн": "ru_18",
            "vtd": "vtd",
            "втд": "vtd",
            "валентин": "vtd",
            "matrix": "matrix",
            "матрица": "matrix",
            "jetix": "jetix",
            "джетикс": "jetix",
        }
        self.secret_buffer = ""
        self.physical_secret_buffer = ""
        self.secret_buffer_limit = max(len(code) for code in self.secret_codes) + 8
        self.secret_cooldown = 0
        self.held_scancodes = set()
        self.secret_overlay = None
        self.secret_timer = 0
        self.secret_image = None
        self.last_secret_image = None
        self.matrix_timer = 0
        self.jetix_timer = 0
        self.vtd_channel = pygame.mixer.Channel(7) if pygame.mixer.get_init() else None
        self.vtd_active = False
        self.vtd_locked = False
        self.meta_video_name = None
        self.meta_video_after = None
        self.meta_video_tick = 0
        self.meta_video_last_index = -1
        self.meta_video_surface = None
        self.meta_video_music_state = None
        self.meta_video_manifest = {}
        self.meta_video_channel = pygame.mixer.Channel(4) if pygame.mixer.get_init() else None
        manifest_path = META_VIDEO_DIR / "manifest.json"
        if manifest_path.exists():
            try:
                self.meta_video_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                self.meta_video_manifest = {}
        self.jetix_logo = None
        if JETIX_LOGO.exists():
            try:
                self.jetix_logo = pygame.image.load(str(JETIX_LOGO)).convert_alpha()
            except pygame.error:
                pass
        self.voice_channel = pygame.mixer.Channel(6) if pygame.mixer.get_init() else None
        self.voice_paths = {name: VOICE_DIR / fn for name, fn in {
            "porn": "porn_reaction.mp3", "start": "meridian_mine.mp3", "200": "lines_200_rage.mp3",
            "tetris": "not_bad.mp3", "dark": "dark_side.mp3", "pause_hint": "pause_hint.mp3",
            "hold_hint": "hold_hint.mp3", "caleb": "rebel.mp3", "rotate_hint": "rotate_hint.mp3",
            "layout": "layout_wont_help.mp3", "blunk_angry": "blunk_angry.mp3",
            "blunk_annoyed": "blunk_annoyed.mp3", "guardian": "guardian_of_veil.mp3",
            "will": "crystal.mp3", "knights": "knights_forward.mp3", "matrix_fan": "matrix_fan.mp3",
            "name_traitors": "extra/name_traitors.wav", "lets_begin": "extra/lets_begin.wav",
            "well": "extra/well.wav", "anger": "extra/anger.wav", "hurry": "extra/hurry.wav",
            "brilliant": "extra/brilliant.wav", "brilliant_laugh": "extra/brilliant_laugh.wav",
            "need_crystal": "extra2/need_crystal.wav", "well_girls": "extra2/well_girls.wav",
            "destroy_weak_link": "extra2/destroy_weak_link.wav",
            "expected_no_less": "extra2/expected_no_less.wav",
            "you_loser": "extra2/you_loser.wav", "your_power_is_nothing": "extra2/your_power_is_nothing.wav",
            "last_hope_universe": "extra2/last_hope_universe.wav", "new_era_phobos": "extra2/new_era_phobos.wav",
            "no_need_to_hurry": "extra2/no_need_to_hurry.wav", "waiting_achieves": "extra2/waiting_achieves.wav",
            "whats_wrong_short": "extra2/whats_wrong_short.wav", "whats_wrong_full": "extra2/whats_wrong_full.wav",
            "what_do_you_want": "extra2/what_do_you_want.wav",
            "pay_short": "extra2/you_will_pay_short.wav", "pay_full": "extra2/you_will_pay_full.wav",
            "cant_end": "extra2/cant_end_like_this.wav", "rage_roar": "extra2/rage_roar.wav",
            "why_failed": "extra2/why_plan_failed.wav"}.items()}
        will_dir = VOICE_DIR.parent / "will"
        self.will_tetris_paths = [p for p in (
            will_dir / "we_are_one.wav", will_dir / "one_short.wav",
            will_dir / "we_are_one_2.wav", will_dir / "we_are_one_3.wav"
        ) if p.exists()]
        self.blunk_voice_dir = VOICE_DIR.parent / "blunk"
        self.caleb_voice_dir = VOICE_DIR.parent / "caleb"
        self.pause_reaction_pool = [
            self.voice_paths.get("well"), self.voice_paths.get("no_need_to_hurry"),
            self.voice_paths.get("waiting_achieves"), self.voice_paths.get("whats_wrong_short"),
            self.voice_paths.get("whats_wrong_full"), self.voice_paths.get("what_do_you_want"),
        ]
        self.pause_reaction_pool = [p for p in self.pause_reaction_pool if p and p.exists()]
        guardians_dir = VOICE_DIR.parent / "guardians"
        self.element_voice_paths = {
            "I": [p for p in (guardians_dir / "cornelia").glob("earth_*.wav")],
            "S": [p for p in (guardians_dir / "irma").glob("water_*.wav")],
            "J": [p for p in (guardians_dir / "taranee").glob("fire_*.wav")],
            "L": [p for p in (guardians_dir / "haylin").glob("air_*.wav")],
        }
        self.menu_voice_channel = pygame.mixer.Channel(5) if pygame.mixer.get_init() else None
        self.sfx_channel = pygame.mixer.Channel(4) if pygame.mixer.get_init() else None
        # Menu navigation is deliberately silent. Phobos still speaks during
        # actual gameplay/cutscenes, but no longer reads main- or pause-menu
        # entries aloud.
        self.menu_voice_paths = []
        self.pause_voice_paths = []
        self.menu_voice_pending = None
        self.menu_voice_delay = 0
        self.pause_voice_pending = None
        self.pause_voice_delay = 0
        self.last_menu_voice_index = None
        self.rotation_hint_block_pieces = 0
        self.queued_voice = None
        self.queued_voice_delay = 0
        self.heart_image = None
        heart_path = EFFECT_DIR / "heart_kandrakar.png"
        if heart_path.exists():
            try:
                self.heart_image = make_border_black_transparent(
                    pygame.image.load(str(heart_path)).convert_alpha(), threshold=18
                )
            except pygame.error: pass
        self.heart_sfx = None
        self.line_clear_sfx = []
        if pygame.mixer.get_init():
            for lightning_path in (SFX_DIR / "line_clear_a.wav", SFX_DIR / "line_clear_b.wav"):
                if lightning_path.exists():
                    try:
                        snd = pygame.mixer.Sound(str(lightning_path)); snd.set_volume(0.78); self.line_clear_sfx.append(snd)
                    except pygame.error: pass
        heart_sfx_path = SFX_DIR / "heart_portal.wav"
        if pygame.mixer.get_init() and heart_sfx_path.exists():
            try: self.heart_sfx = pygame.mixer.Sound(str(heart_sfx_path)); self.heart_sfx.set_volume(0.85)
            except pygame.error: pass
        self.pending_clear = None
        # v6.21: persistent character toggles + silent fourth-wall Phobos room.
        self.character_labels = {"I":"CORNELIA / I", "J":"TARANEE / J", "L":"HAY LIN / L", "T":"CALEB / T", "O":"BLUNK / O", "S":"IRMA / S", "Z":"WILL / Z"}
        self.character_enabled = {k: True for k in PIECES}
        self.phobos_enabled = True
        self.settings_index = 0
        self.settings_page = "root"
        self.settings_message = ""
        self.start_speed = 1
        self.figure_fall_mode = "phobos"
        self.classic_piece_queue = []
        self.classic_piece_signature = ()
        self.empty_roster_started_ms = None
        self.empty_roster_bored = False
        self.empty_roster_bored_at = None
        self.load_settings()
        self.phobos_deleted_win = False
        self.phobos_room_data = {"random_chains": [], "event_reactions": {}, "spam_reactions": []}
        rp = PHOBOS_ROOM_DIR / "replicas.json"
        if rp.exists():
            try: self.phobos_room_data = json.loads(rp.read_text(encoding="utf-8"))
            except Exception: pass
        self.phobos_room_bg = None
        # v6.37.1 room composite: the supplied interior, fiery Meridian view
        # and table are one stable background, so they cannot drift apart.
        bgp = PHOBOS_ROOM_DIR / "background_v2.png"
        if not bgp.exists():
            bgp = PHOBOS_ROOM_DIR / "background.png"
        if bgp.exists():
            try: self.phobos_room_bg = pygame.image.load(str(bgp)).convert()
            except pygame.error: pass
        # Keep the supplied exterior as a separate runtime layer. This is
        # intentionally independent from the interior/desk composite so a
        # future 3DS port can move or replace the view without rebuilding the
        # room art.
        self.phobos_room_outside = None
        outside_fp = ASSET_DIR / "reference" / "v6371_user_materials" / "meridian_fire_view_source.png"
        if outside_fp.exists():
            try:
                outside = pygame.image.load(str(outside_fp)).convert()
                self.phobos_room_outside = pygame.transform.smoothscale(outside, (520, 370))
            except pygame.error:
                self.phobos_room_outside = None
        self.phobos_room_bg_frames=[]
        if bgp.name != "background_v2.png":
            for _fp in sorted((PHOBOS_ROOM_DIR / "bg_frames").glob("room_*.jpg")):
                try: self.phobos_room_bg_frames.append(pygame.image.load(str(_fp)).convert())
                except pygame.error: pass
        # Use the new six-pose seated sheet. Its opaque light canvas is removed
        # from each 512x512 cell without black-keying the costume.
        self.phobos_room_emotions = []
        seated_sheet_fp = PHOBOS_ROOM_DIR / "phobos_seated_poses.png"
        if seated_sheet_fp.exists():
            try:
                seated_sheet = pygame.image.load(str(seated_sheet_fp)).convert_alpha()
                cell_w, cell_h = seated_sheet.get_width() // 3, seated_sheet.get_height() // 2
                for row in range(2):
                    for column in range(3):
                        frame = seated_sheet.subsurface(
                            pygame.Rect(column * cell_w, row * cell_h, cell_w, cell_h)
                        ).copy()
                        frame = make_border_light_transparent(frame)
                        bounds = frame.get_bounding_rect(min_alpha=8)
                        if bounds.width and bounds.height:
                            self.phobos_room_emotions.append(frame.subsurface(bounds).copy())
            except pygame.error:
                self.phobos_room_emotions = []
        if not self.phobos_room_emotions:
            state_files = sorted((PHOBOS_ROOM_DIR / "states").glob("state_*.png"))
            for fp in state_files:
                try: self.phobos_room_emotions.append(load_clean_alpha(fp))
                except pygame.error: pass
        self.phobos_room_emotion = 0
        self.phobos_room_table = None
        table_fp = PHOBOS_ROOM_DIR / "table_foreground.png"
        if table_fp.exists():
            try: self.phobos_room_table = pygame.image.load(str(table_fp)).convert_alpha()
            except pygame.error: pass
        self.mg_art = {}
        mg_art_dir = ASSET_DIR / "minigames"
        for key in ("phobos_face","will_face","irma_face","blunk_face","cedric_face","cornelia","caleb","taranee","haylin_face","haylin_flight","will_enemy_1","will_enemy_2","will_enemy_3","will_enemy_4"):
            fp = mg_art_dir / (key + ".png")
            if fp.exists():
                try: self.mg_art[key] = load_clean_alpha(fp)
                except pygame.error: pass
        if "taranee" in self.mg_art:
            self.mg_art["taranee_face"] = self.mg_art["taranee"].copy()
        # Runner/shooter/garden need the supplied full-body action poses rather
        # than the old small portrait crops.
        for key,fp in {
            "caleb": LINES100_DIR/"caleb_action.png",
            "taranee": LINES100_DIR/"taranee_action.png",
            "cornelia": LINES100_DIR/"cornelia_action.png",
        }.items():
            if fp.exists():
                try: self.mg_art[key]=load_clean_alpha(fp)
                except pygame.error: pass
        haylin_bg_fp = BACKGROUND_DIR / "phase_0_99_throne.png"
        if haylin_bg_fp.exists():
            try: self.mg_art["haylin_bg"] = pygame.image.load(str(haylin_bg_fp)).convert()
            except pygame.error: pass
        heart_fp = EFFECT_DIR / "heart_kandrakar.png"
        if heart_fp.exists():
            try: self.mg_art["heart_kandrakar"] = load_clean_alpha(heart_fp, threshold=18)
            except pygame.error: pass
        self.phobos_type_sound = None
        type_fp = ASSET_DIR / "audio" / "collection" / "phobos_type_tick.wav"
        if pygame.mixer.get_init() and type_fp.exists():
            try:
                self.phobos_type_sound = pygame.mixer.Sound(str(type_fp)); self.phobos_type_sound.set_volume(0.22)
            except pygame.error:
                self.phobos_type_sound = None
        self.phobos_room_chain = None
        self.phobos_room_line = 0
        self.phobos_room_next_ms = 0
        self.phobos_room_wait_until = 0
        self.phobos_room_recent = []
        self.phobos_room_key_count = 0
        self.phobos_room_key_suppressed = False
        self.phobos_room_right_shift_seen = False
        self.phobos_room_reaction = None
        self.phobos_room_reaction_until = 0
        self.phobos_room_intro_pending = True
        self.phobos_tetris_laughs = sorted((SFX_DIR / "phobos_laughs").glob("*.wav"))
        if not self.phobos_tetris_laughs and self.voice_paths.get("brilliant_laugh"):
            self.phobos_tetris_laughs = [self.voice_paths["brilliant_laugh"]]
        self.phobos_scream_pool = [q for q in (self.voice_paths.get("rage_roar"), self.blunk_voice_dir / "groan.wav") if q and q.exists()]
        self.reset()
        # v6.34: restore the real opening intro on application launch.
        # restart_intro() owns self.mode and the intro soundtrack takes over on draw.
        self.restart_intro()
        self.music.set_phase(-1, force=True)
        self.music.stop()

    def reset(self):
        if getattr(self, "vtd_channel", None):
            self.vtd_channel.stop()
        self.vtd_active = False
        if hasattr(self, "music"):
            self.music.special_lock = False
        self.record_saved = False
        self.pending_clear = None
        self.board = [[None for _ in range(BOARD_W)] for _ in range(BOARD_H)]
        self.lines = 0
        self.score = 0
        self.paused = False
        self.game_over = False
        self.game_over_voice_handled = False
        if not hasattr(self, "consecutive_game_overs"):
            self.consecutive_game_overs = 0
        self.story_overlay = None
        self.story_seen = set()
        self.story100_tick = 0
        self.story100_stage = "idle"
        self.story100_sfx_played = set()
        # v6.18 third cutscene / meta-route state.
        self.winner_choice = 0  # 0 Guardians, 1 Phobos
        self.story200_stage = "choice"
        self.story200_tick = 0
        self.story_winner = None
        self.phobos_route = False
        self.guardians_route = False
        self.guardians_gone_this_run = False
        self.horror_piece_mode = False
        self.phobos_room = False
        self.phobos_room_layout = "table"
        self.phobos_room_stage = "idle"
        self.phobos_room_tick = 0
        self.phobos_room_last_voice = 0
        self.phobos_room_last_key = None
        self.phobos_room_caption = ""
        self.phobos_room_chain = None
        self.phobos_room_line = 0
        self.phobos_room_next_ms = 0
        self.phobos_room_wait_until = 0
        self.phobos_room_recent = []
        self.phobos_room_key_count = 0
        self.phobos_room_key_suppressed = False
        self.phobos_room_right_shift_seen = False
        self.phobos_room_reaction = None
        self.phobos_room_reaction_until = 0
        self.phobos_deleted_win = False
        self.empty_roster_started_ms = None
        self.empty_roster_bored = False
        self.empty_roster_bored_at = None
        self.secret_overlay = None
        self.secret_timer = 0
        self.secret_image = None
        self.matrix_timer = 0
        self.jetix_timer = 0
        self.secret_buffer = ""
        self.physical_secret_buffer = ""
        self.secret_cooldown = 0
        self.held_scancodes.clear()
        self.hold_kind = None
        self.hold_used = False
        self.pause_menu_items = ["CONTINUE", "RESTART", "MAIN MENU"]
        self.pause_menu_index = 0
        self.game_over_items = ["RESTART", "MAIN MENU"]
        self.game_over_index = 0
        self.play_frames = 0
        self.pause_hint_played = False
        self.pause_hint_eligible_at = random.randint(FPS * 150, FPS * 420)
        self.hold_count_window = 0
        self.voice_cooldown = 0
        self.spawn_history = []
        self.last_seen_piece = {k: 0 for k in PIECES}
        self.piece_serial = 0
        self.classic_piece_queue = []
        self.classic_piece_signature = ()
        self.rotation_count = 0
        self.rotation_hint_block_pieces = 0
        self.spawn_voice_used = set()
        self.pause_reaction_used = set()
        self.queued_voice = None
        self.queued_voice_delay = 0
        self.pause_voice_pending = None
        self.pause_voice_delay = 0
        self.vtd_intro_timer = 0
        self.vtd_locked = False
        self.meta_video_name = None
        self.meta_video_after = None
        self.meta_video_tick = 0
        self.meta_video_last_index = -1
        self.meta_video_surface = None
        self.meta_video_music_state = None
        self.last_layout = None
        self.layout_reaction_done = False
        self.next_kind = self.random_piece()
        self.current = None
        self.frame_counter = 0
        if self.next_kind is not None:
            self.spawn_piece()
        else:
            # Truly empty roster: no fallback tetromino is generated.
            self.empty_roster_started_ms = pygame.time.get_ticks()
        self.music.set_phase(0, force=True)

    def phase_index(self):
        if self.lines >= LINES_PHASE2:
            return 2
        if self.lines >= LINES_RESISTANCE:
            return 1
        return 0

    def gameplay_background_phase(self):
        """Route-specific backdrop after the 200-line choice."""
        if self.lines >= LINES_PHASE2:
            if self.phobos_route:
                return 1  # keep the darker Resistance/Phobos background
            if self.guardians_route:
                return 2  # liberated/light 200+ background
        return self.phase_index()

    def plain_piece_mode(self):
        """200+ vanilla branches use true classic blocks with no character artwork."""
        return self.lines >= LINES_PHASE2 and (self.guardians_route or (self.phobos_route and not self.horror_piece_mode))

    def draw_plain_cell(self, rect, kind, inset=1):
        # Classic glossy/bevel blocks matching the reference vanilla tetromino sheet.
        col = PLAIN_TETRIS_COLORS.get(kind, COLORS["accent"])
        inner = rect.inflate(-inset*2, -inset*2)
        pygame.draw.rect(self.canvas, col, inner)
        hi = tuple(min(255, int(c*0.45)+150) for c in col)
        mid = tuple(max(0, int(c*0.78)) for c in col)
        lo = tuple(max(0, int(c*0.55)) for c in col)
        b = max(4, inner.width//7)
        # top shine, left mid bevel, right/bottom shadow — no character artwork.
        pygame.draw.polygon(self.canvas, hi, [inner.topleft, inner.topright, (inner.right-b,inner.top+b), (inner.left+b,inner.top+b)])
        pygame.draw.polygon(self.canvas, mid, [inner.topleft, (inner.left+b,inner.top+b), (inner.left+b,inner.bottom-b), inner.bottomleft])
        pygame.draw.polygon(self.canvas, lo, [inner.topright, inner.bottomright, (inner.right-b,inner.bottom-b), (inner.right-b,inner.top+b)])
        pygame.draw.polygon(self.canvas, lo, [inner.bottomleft, (inner.left+b,inner.bottom-b), (inner.right-b,inner.bottom-b), inner.bottomright])
        pygame.draw.rect(self.canvas, col, (inner.left+b, inner.top+b, max(1,inner.width-2*b), max(1,inner.height-2*b)))

    def draw_plain_piece(self, kind, rotation, gx, gy):
        for dx, dy in SHAPES[kind][rotation]:
            r = pygame.Rect(BOARD_X + (gx+dx)*CELL, BOARD_Y + (gy+dy)*CELL, CELL, CELL)
            self.draw_plain_cell(r, kind)

    def enter_phobos_room(self, source="lines"):
        """Enter the inescapable room and revoke the normal game's controls.

        Besides the 300-line trigger, defeat after choosing Phobos now opens
        the room immediately. Secret buffers and active Easter-egg overlays
        are cleared so no old game code can execute inside Phobos's scene.
        """
        if self.game_over:
            self.save_record()
        self.game_over = False
        self.game_over_voice_handled = False
        self.story_seen.add(300)
        self.story_overlay = 300
        self.phobos_room = True
        self.phobos_room_stage = "crash"
        self.phobos_room_tick = 0
        self.phobos_room_layout = "table"
        self.phobos_room_last_voice = 0
        self.phobos_room_last_key = None
        self.phobos_room_caption = ""
        self.phobos_room_chain = None
        self.phobos_room_next_ms = pygame.time.get_ticks() + 3000
        self.phobos_room_wait_until = 0
        self.phobos_room_key_count = 0
        self.phobos_room_key_suppressed = False
        self.phobos_room_right_shift_seen = False
        self.phobos_room_intro_pending = True
        self.secret_buffer = ""
        self.physical_secret_buffer = ""
        self.secret_overlay = None
        self.secret_timer = 0
        self.secret_image = None
        self.matrix_timer = 0
        self.jetix_timer = 0
        self.queued_voice = None
        self.queued_voice_delay = 0
        if self.voice_channel:
            self.voice_channel.stop()
        if self.menu_voice_channel:
            self.menu_voice_channel.stop()
        if self.vtd_channel:
            self.vtd_channel.stop()
        self.vtd_active = False
        self.vtd_locked = False
        self.music.special_lock = False
        self.music.stop()

    def choose_phobos_room_chain(self):
        pool = self.phobos_room_data.get("random_chains", [])
        if not pool: return
        eligible = [x for x in pool if x.get("id") not in self.phobos_room_recent[-8:]] or pool
        chain = random.choice(eligible)
        self.phobos_room_chain = chain
        self.phobos_room_line = 0
        self.phobos_room_type_started_ms = pygame.time.get_ticks()
        self.phobos_room_type_complete = False
        self.phobos_room_recent.append(chain.get("id"))
        self.phobos_room_recent = self.phobos_room_recent[-10:]
        if self.phobos_room_emotions:
            self.phobos_room_emotion = random.randrange(len(self.phobos_room_emotions))
        self.phobos_room_next_ms = pygame.time.get_ticks() + 40000
        self.phobos_room_wait_until = 0

    def current_phobos_room_text(self):
        if self.phobos_room_reaction and pygame.time.get_ticks() < self.phobos_room_reaction_until:
            return self.phobos_room_reaction
        if not self.phobos_room_chain: return ""
        lines = self.phobos_room_chain.get("lines", [])
        if not lines: return ""
        i=min(self.phobos_room_line,len(lines)-1)
        line=lines[i]
        if line.startswith("[WAIT"):
            return "..."
        if not self.phobos_room_type_started_ms: self.phobos_room_type_started_ms=pygame.time.get_ticks()
        count=max(0,(pygame.time.get_ticks()-self.phobos_room_type_started_ms)//38)
        self.phobos_room_type_complete = count >= len(line)
        return line if self.phobos_room_type_complete else line[:count]

    def advance_phobos_room_line(self):
        if not self.phobos_room_chain: return
        now=pygame.time.get_ticks()
        if self.phobos_room_wait_until and now < self.phobos_room_wait_until: return
        if not self.phobos_room_type_complete:
            self.phobos_room_type_started_ms = now - 999999
            self.phobos_room_type_complete = True
            return
        lines=self.phobos_room_chain.get("lines",[])
        if self.phobos_room_line + 1 < len(lines):
            self.phobos_room_line += 1
            self.phobos_room_type_started_ms = now
            self.phobos_room_type_complete = False
            if lines[self.phobos_room_line].startswith("[WAIT"):
                self.phobos_room_wait_until = now + 40000
        else:
            # Final SPACE closes the dialogue completely; the 40 s silence starts now.
            self.phobos_room_chain = None
            self.phobos_room_type_complete = False
            self.phobos_room_next_ms = now + 40000
        if self.phobos_room_emotions and random.random() < 0.45:
            self.phobos_room_emotion=random.randrange(len(self.phobos_room_emotions))

    def phobos_room_key_name(self, key, unicode_char="", mod=0, scancode=None):
        if key == pygame.K_ESCAPE: return "escape"
        if key == pygame.K_a: return "a"
        if key == pygame.K_f: return "f"
        if key == pygame.K_x: return "x"
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER): return "enter"
        if unicode_char == "?": return "question"
        if key == pygame.K_c: return "c"
        if key == pygame.K_LSHIFT: return "left_shift"
        if key == pygame.K_RSHIFT: return "right_shift"
        if key == pygame.K_UP: return "up"
        if key == pygame.K_DOWN: return "down"
        if key == pygame.K_LEFT: return "left"
        if key == pygame.K_RIGHT: return "right"
        if key == pygame.K_w: return "w"
        if key == pygame.K_z: return "z"
        if key == pygame.K_m: return "m"
        if unicode_char in ("ё","Ё","`","~","\\","|"): return "backtick"
        if unicode_char in ("ъ","Ъ","]","}"): return "bracket"
        if key == pygame.K_q and (mod & pygame.KMOD_SHIFT): return "dev_q"
        if key == pygame.K_F11 or (key in (pygame.K_RETURN,pygame.K_KP_ENTER) and (mod & (pygame.KMOD_META|pygame.KMOD_ALT))): return "fullscreen"
        return None

    def react_phobos_room_key(self, key, unicode_char="", mod=0, scancode=None):
        if key in (pygame.K_SPACE, pygame.K_RETURN) and self.phobos_room_chain:
            self.advance_phobos_room_line(); return
        name=self.phobos_room_key_name(key,unicode_char,mod,scancode)
        if not name: return
        if name == "right_shift" and self.phobos_room_right_shift_seen: return
        if self.phobos_room_key_suppressed: return
        self.phobos_room_key_count += 1
        if self.phobos_room_key_count >= 15:
            chain={"id":"final_key_silence","lines":["Я больше не собираюсь комментировать нажатия.","Развлекай себя сам."]}
            self.phobos_room_key_suppressed=True
        elif self.phobos_room_key_count >= 10 and self.phobos_room_data.get("spam_reactions"):
            raw=random.choice(self.phobos_room_data["spam_reactions"]); chain={"id":"spam","lines":raw if isinstance(raw,list) else [str(raw)]}
        else:
            event_map={"escape":"escape","right_shift":"right_shift"}
            pool=self.phobos_room_data.get("event_reactions",{}).get(event_map.get(name,name),[])
            if pool:
                raw=random.choice(pool); lines=raw if isinstance(raw,list) else [str(raw)]
            elif name=="escape": lines=["Escape?", "Нет. Здесь это так не работает."]
            elif name=="right_shift": lines=["Правый Shift.","У разработчика эта кнопка не работала как ожидалось, поэтому он не привязывал к ней реплики."]
            else: lines=[f"{name}. Любопытно."]
            chain={"id":"key_"+name,"lines":lines}
        self.phobos_room_chain=chain; self.phobos_room_line=0; self.phobos_room_type_started_ms=pygame.time.get_ticks(); self.phobos_room_type_complete=False
        self.phobos_room_wait_until=0; self.phobos_room_next_ms=10**12
        if name=="right_shift": self.phobos_room_right_shift_seen=True
        if self.phobos_room_emotions: self.phobos_room_emotion=random.randrange(len(self.phobos_room_emotions))

    def fall_interval(self):
        # Automatic Tetris gravity. Restored in v6.34 after the v6.33 hotfix
        # accidentally dropped this method while update()/HUD still called it.
        # Each START SPEED step is equivalent to 25 speed-lines, while the
        # actual story/score line counter remains untouched.
        speed_lines = self.lines + (max(1, min(5, self.start_speed)) - 1) * 25
        if speed_lines < 25: return 32
        if speed_lines < 50: return 28
        if speed_lines < 75: return 24
        if speed_lines < 100: return 20
        if speed_lines < 125: return 17
        if speed_lines < 150: return 14
        if speed_lines < 175: return 11
        if speed_lines < 200: return 9
        return max(3, 8 - (speed_lines - 200) // 50)

    def play_voice(self, name, force=False):
        # v6.33 hard safety: the spoken line “Заклинание Фобоса рушится” is forbidden everywhere.
        banned = {"phobos_spell_break", "spell_break", "zaklinanie_fobosa_rushitsya"}
        if str(name).lower() in banned:
            return False
        if self.guardians_route and name not in ("matrix_fan",):
            return False
        if not self.voice_channel or (self.voice_cooldown > 0 and not force):
            return False
        path = self.voice_paths.get(name)
        if not path or not path.exists():
            return False
        try:
            self.voice_channel.stop()
            snd = pygame.mixer.Sound(str(path)); snd.set_volume(1.0)
            self.voice_channel.play(snd)
            self.music.duck(True)
            if self.vtd_channel: self.vtd_channel.set_volume(0.28)
            self.voice_cooldown = FPS * 18
            return True
        except pygame.error as exc:
            print(f"[voice] {exc}")
            return False

    def play_external_voice(self, path, force=False):
        if path and ("phobos_spell_break" in str(path).lower() or "заклинание фобоса руш" in str(path).lower()):
            return False
        # Once the Guardians win, Phobos is completely gone from gameplay audio,
        # including queued/"external" lines and pause reactions.
        try:
            is_phobos = VOICE_DIR in path.parents or path.parent == VOICE_DIR
            is_guardian = (VOICE_DIR.parent / "guardians") in path.parents
        except Exception:
            is_phobos = is_guardian = False
        if self.guardians_route and is_phobos:
            return False
        if self.guardians_gone_this_run and is_guardian:
            return False
        if not self.voice_channel or (self.voice_cooldown > 0 and not force) or not path.exists():
            return False
        try:
            self.voice_channel.stop()
            snd = pygame.mixer.Sound(str(path)); snd.set_volume(1.0)
            self.voice_channel.play(snd)
            self.music.duck(True)
            if self.vtd_channel: self.vtd_channel.set_volume(0.28)
            self.voice_cooldown = FPS * 18
            return True
        except pygame.error:
            return False

    def play_voice_if_idle(self, name):
        """Play a hint despite the long global cooldown, but never interrupt speech already playing."""
        if self.guardians_route:
            return False
        if not self.voice_channel or self.voice_channel.get_busy():
            return False
        path = self.voice_paths.get(name)
        if not path or not path.exists():
            return False
        try:
            snd = pygame.mixer.Sound(str(path)); snd.set_volume(1.0)
            self.voice_channel.play(snd)
            self.music.duck(True)
            if self.vtd_channel: self.vtd_channel.set_volume(0.28)
            self.voice_cooldown = FPS * 18
            return True
        except pygame.error:
            return False

    def queue_external_voice(self, path, delay_frames=0):
        try:
            is_phobos = VOICE_DIR in path.parents or path.parent == VOICE_DIR
            is_guardian = (VOICE_DIR.parent / "guardians") in path.parents
        except Exception:
            is_phobos = is_guardian = False
        if self.guardians_route and is_phobos:
            return
        if self.guardians_gone_this_run and is_guardian:
            return
        self.queued_voice = path
        self.queued_voice_delay = max(0, delay_frames)

    def random_piece(self):
        """Select a piece using the configured Phobos or two-bag randomizer."""
        candidates = [k for k in PIECES if self.character_enabled.get(k, True)]
        if not candidates:
            return None
        if self.figure_fall_mode == "classic":
            signature = tuple(candidates)
            if signature != self.classic_piece_signature:
                self.classic_piece_signature = signature
                self.classic_piece_queue = []
            # Keep two complete shuffled bags queued. Each enabled shape is
            # seen once per bag, and the boundary is swapped when it would
            # repeat the last shape from the previous bag.
            if not self.classic_piece_queue:
                previous = self.spawn_history[-1] if self.spawn_history else None
                for _ in range(2):
                    bag = candidates[:]
                    random.shuffle(bag)
                    boundary = self.classic_piece_queue[-1] if self.classic_piece_queue else previous
                    if boundary and len(bag) > 1 and bag[0] == boundary:
                        swap_at = next(i for i, kind in enumerate(bag[1:], 1) if kind != bag[0])
                        bag[0], bag[swap_at] = bag[swap_at], bag[0]
                    self.classic_piece_queue.extend(bag)
            return self.classic_piece_queue.pop(0)
        # Default Phobos mode: controlled chaos with drought protection, but
        # up to three deliberate repeats are still possible.
        if len(self.spawn_history) >= 3 and len(set(self.spawn_history[-3:])) == 1:
            if self.spawn_history[-1] in candidates and len(candidates) > 1:
                candidates.remove(self.spawn_history[-1])
        weights = []
        for k in candidates:
            drought = max(0, self.piece_serial - self.last_seen_piece.get(k, 0))
            w = 1.0 + min(drought, 14) * 0.075
            if self.spawn_history and self.spawn_history[-1] == k:
                w *= 0.62
                if len(self.spawn_history) >= 2 and self.spawn_history[-2] == k:
                    w *= 0.22
            weights.append(w)
        return random.choices(candidates, weights=weights, k=1)[0]

    def maybe_character_voice(self, kind):
        """Rare character-addressed spawn reactions. Each concrete spawn line can fire once per game."""
        if self.guardians_gone_this_run:
            return
        if not self.character_enabled.get(kind, True): return
        if self.voice_cooldown > 0:
            return

        def once(key, chance, callback):
            if key in self.spawn_voice_used or random.random() >= chance:
                return False
            if callback():
                self.spawn_voice_used.add(key)
                return True
            return False

        if kind == "T":
            if once("caleb_name_traitors", 0.045, lambda: self.play_voice("name_traitors")):
                return
            once("caleb_rebel", 0.025, lambda: self.play_voice("caleb"))
        elif kind == "O":
            candidates = [("blunk_angry", self.voice_paths.get("blunk_angry")),
                          ("blunk_annoyed", self.voice_paths.get("blunk_annoyed"))]
            available = [(k,p) for k,p in candidates if k not in self.spawn_voice_used and p and p.exists()]
            if available and random.random() < 0.035:
                key, path = random.choice(available)
                if self.play_external_voice(path): self.spawn_voice_used.add(key)
        elif kind == "Z":
            # In the actual sprite set Z is Will; S is Irma.
            if once("will_need_crystal", 0.045, lambda: self.play_voice("need_crystal")):
                return
            if once("will_crystal", 0.045, lambda: self.play_voice("will")):
                return
            once("guardians_well_girls", 0.018, lambda: self.play_voice("well_girls"))
        elif kind in ("I", "L", "J", "S"):
            if once("guardians_well_girls", 0.018, lambda: self.play_voice("well_girls")):
                return
            once("guardian_of_veil", 0.008, lambda: self.play_voice("guardian"))

    def spawn_piece(self, kind=None):
        if kind is None:
            kind = self.next_kind
            if kind is None:
                self.current = None
                self.next_kind = None
                if self.empty_roster_started_ms is None:
                    self.empty_roster_started_ms = pygame.time.get_ticks()
                return False
            self.spawn_history.append(kind)
            self.spawn_history = self.spawn_history[-8:]
            self.piece_serial += 1
            if self.rotation_hint_block_pieces > 0:
                self.rotation_hint_block_pieces -= 1
            self.last_seen_piece[kind] = self.piece_serial
            self.next_kind = self.random_piece()
        self.current = {"kind": kind, "rot": 0, "x": 3, "y": 0}
        self.rotation_count = 0
        self.hold_used = False
        self.maybe_character_voice(kind)
        if self.collides(self.current["x"], self.current["y"], self.current["rot"]):
            self.game_over = True
            if self.phobos_route and self.story_winner == "phobos":
                self.enter_phobos_room("phobos_defeat")
            else:
                self.music.pause()
        return True

    def shape(self, rot=None):
        if self.current is None:
            return []
        if rot is None:
            rot = self.current["rot"]
        return SHAPES[self.current["kind"]][rot]

    def collides(self, x, y, rot):
        if self.current is None:
            return False
        for dx, dy in SHAPES[self.current["kind"]][rot]:
            bx, by = x + dx, y + dy
            if bx < 0 or bx >= BOARD_W or by >= BOARD_H:
                return True
            if by >= 0 and self.board[by][bx] is not None:
                return True
        return False

    def move(self, dx, dy):
        if self.current is None:
            return False
        nx, ny = self.current["x"] + dx, self.current["y"] + dy
        if not self.collides(nx, ny, self.current["rot"]):
            self.current["x"], self.current["y"] = nx, ny
            return True
        return False

    def rotate(self):
        if self.current is None:
            return False
        self.rotation_count += 1
        # From the 5th spin onward Phobos becomes increasingly likely to comment.
        # 5th=12%, 6th=24%, 7th=38%, 8th=55%, 9th+=72%; once per piece.
        if self.rotation_count >= 5 and self.rotation_hint_block_pieces <= 0:
            spin_chance = {5: 0.12, 6: 0.24, 7: 0.38, 8: 0.55}.get(self.rotation_count, 0.72)
            if random.random() < spin_chance and self.play_voice_if_idle("rotate_hint"):
                self.rotation_count = -999
                # Five subsequent spawned pieces are immune to this particular hint.
                self.rotation_hint_block_pieces = 6
        nr = (self.current["rot"] + 1) % 4
        # Small wall-kick set, enough for the current prototype.
        for kick in (0, -1, 1, -2, 2):
            nx = self.current["x"] + kick
            if not self.collides(nx, self.current["y"], nr):
                self.current["x"] = nx
                self.current["rot"] = nr
                return

    def hard_drop(self):
        if self.current is None:
            return
        n = 0
        while self.move(0, 1):
            n += 1
        self.score += n * 2
        self.lock_piece()

    def hold(self):
        if self.current is None:
            return False
        if self.hold_used:
            return
        current_kind = self.current["kind"]
        if self.hold_kind is None:
            self.hold_kind = current_kind
            self.spawn_piece()
        else:
            swap = self.hold_kind
            self.hold_kind = current_kind
            self.current = {"kind": swap, "rot": 0, "x": 3, "y": 0}
            if self.collides(self.current["x"], self.current["y"], 0):
                self.game_over = True
                if self.phobos_route and self.story_winner == "phobos":
                    self.enter_phobos_room("phobos_defeat")
                else:
                    self.music.pause()
        self.hold_used = True
        self.hold_count_window += 1
        if self.hold_count_window >= 7 and random.random() < 0.35:
            if self.play_voice("hold_hint"):
                self.hold_count_window = 0

    def lock_piece(self):
        if self.current is None:
            return
        kind = self.current["kind"]
        rot = self.current["rot"]
        for dx, dy in SHAPES[kind][rot]:
            bx, by = self.current["x"] + dx, self.current["y"] + dy
            if 0 <= by < BOARD_H:
                if self.plain_piece_mode():
                    self.board[by][bx] = {"kind": kind, "surface": None, "plain": True}
                else:
                    frag = self.sprites.cell_surface(kind, rot, (dx, dy), self.phase_index(), horror=self.horror_piece_mode and self.phobos_route)
                    self.board[by][bx] = {"kind": kind, "surface": frag.copy() if frag else None, "plain": False}
        rows = [y for y, row in enumerate(self.board) if all(cell is not None for cell in row)]
        if rows:
            # Fast clear animation: 1-3 rows = lightning; 4 = Heart of Kandrakar pulse.
            frames = 24 if len(rows) == 4 else 10
            self.last_clear_kind = kind
            self.pending_clear = {"rows": rows, "kind": kind, "frames": frames, "total": frames}
            if self.phobos_route:
                # Phobos ending: no Kandrakar sound; line clears are dark magic + screams.
                if self.phobos_scream_pool:
                    self.queue_external_voice(random.choice(self.phobos_scream_pool), delay_frames=0)
                if len(rows) == 4 and self.phobos_tetris_laughs:
                    self.queue_external_voice(random.choice(self.phobos_tetris_laughs), delay_frames=3)
            elif len(rows) == 4 and self.heart_sfx:
                if self.sfx_channel: self.sfx_channel.play(self.heart_sfx)
                else: self.heart_sfx.play()
            elif len(rows) < 4 and self.line_clear_sfx:
                snd = random.choice(self.line_clear_sfx)
                if self.sfx_channel: self.sfx_channel.play(snd)
                else: snd.play()
            return
        self.finish_lock(0)

    def finish_lock(self, cleared):
        before = self.lines
        clear_kind = None
        if cleared and getattr(self, "last_clear_kind", None):
            clear_kind = self.last_clear_kind
        if cleared:
            self.lines += cleared
            self.score += [0, 100, 300, 500, 800][min(cleared, 4)]
            if self.phobos_route and before < 300 <= self.lines:
                self.enter_phobos_room("lines")
                return
            if self.phobos_route:
                # In Phobos's ending, figure dialogue is replaced by screams; Tetris uses his laugh only.
                pass
            elif cleared == 4:
                # Will may speak only if Will/Z still exists. The Heart itself is an artifact, not a character.
                if self.sfx_channel and self.sfx_channel.get_busy():
                    self.sfx_channel.fadeout(100)
                will_exists = self.character_enabled.get("Z", True)
                if will_exists and self.will_tetris_paths:
                    self.play_external_voice(random.choice(self.will_tetris_paths), force=True)
                    if random.random() < 0.55:
                        self.queued_voice = self.voice_paths.get("tetris")
                        self.queued_voice_delay = FPS // 8
                elif random.random() < 0.55:
                    # No Will line when Will is deleted; Phobos may still make his normal pre-victory reaction.
                    self.play_voice("tetris", force=True)
            else:
                # A rare Phobos interruption can replace the character reaction on a normal clear.
                phobos_override = random.random() < 0.05 and self.voice_paths.get("destroy_weak_link") and self.voice_paths["destroy_weak_link"].exists()
                if phobos_override:
                    self.queue_external_voice(self.voice_paths["destroy_weak_link"], delay_frames=2)
                elif clear_kind in self.element_voice_paths and self.element_voice_paths[clear_kind]:
                    # I=Cornelia, J=Taranee, L=Hay Lin, S=Irma. Z=Will deliberately has no elemental word.
                    self.queue_external_voice(random.choice(self.element_voice_paths[clear_kind]), delay_frames=2)
                elif clear_kind == "T":
                    # Caleb: the line works as a line-clear reaction, not a spawn greeting.
                    p = self.caleb_voice_dir / "im_15.wav"
                    if p.exists() and random.random() < 0.40:
                        self.queue_external_voice(p, delay_frames=2)
                elif clear_kind == "O":
                    # O/Blunk is 2x2: it can complete only one or two rows. Never attach 3/4-line reactions.
                    if cleared == 1:
                        pool = [self.blunk_voice_dir / "businessman.wav", self.blunk_voice_dir / "laugh.wav", self.blunk_voice_dir / "groan.wav", self.blunk_voice_dir / "fight.wav"]
                        chance = 0.68
                    elif cleared == 2:
                        pool = [self.blunk_voice_dir / "also_warrior.wav", self.blunk_voice_dir / "treasure.wav", self.blunk_voice_dir / "not_afraid.wav"]
                        chance = 0.82
                    else:
                        pool, chance = [], 0.0
                    pool = [p for p in pool if p.exists()]
                    if pool and random.random() < chance:
                        self.queue_external_voice(random.choice(pool), delay_frames=2)
        old_phase = 0 if before < LINES_RESISTANCE else 1 if before < LINES_PHASE2 else 2
        if before < LINES_RESISTANCE <= self.lines and 100 not in self.story_seen:
            self.story_seen.add(100)
            self.start_story100()
        elif before < LINES_PHASE2 <= self.lines and 200 not in self.story_seen:
            self.story_seen.add(200)
            self.consecutive_game_overs = 0
            self.story_overlay = 200
            self.story200_stage = "cinematic_reverse"
            self.story200_tick = 0
            self.winner_choice = 0
            self.music.pause()
        elif self.phobos_route and self.lines >= 300 and 300 not in self.story_seen:
            self.enter_phobos_room("lines")
        elif self.phase_index() != old_phase:
            self.music.set_phase(self.phase_index(), force=True)
        self.last_clear_kind = None
        self.spawn_piece()

    def resolve_pending_clear(self):
        if not self.pending_clear: return
        rows = set(self.pending_clear["rows"])
        kept = [row for y, row in enumerate(self.board) if y not in rows]
        cleared = len(rows)
        self.board = [[None for _ in range(BOARD_W)] for _ in range(cleared)] + kept
        self.pending_clear = None
        self.finish_lock(cleared)

    def story200_choice_active(self):
        return self.mode == "game" and self.story_overlay == 200 and self.story200_stage == "choice"

    def begin_meta_video(self, name, after):
        self.meta_video_music_state = {
            "phase": self.music.phase,
            "paused": self.music.paused,
            "enabled": self.music.enabled,
        }
        # MATRIX/PORN audio must own the output completely. Pausing was not
        # reliable on every mixer backend, so stop the background stream.
        self.music.enter_special()
        for channel in (self.voice_channel, self.menu_voice_channel, self.vtd_channel):
            if channel:
                channel.stop()
        info = self.meta_video_manifest.get(name)
        if not info:
            # No prepared video: still follow the route instead of falling back to the normal secret effect.
            self.meta_video_after = after
            self.finish_meta_video()
            return
        self.meta_video_name = name
        self.meta_video_after = after
        self.meta_video_tick = 0
        self.meta_video_started_ms = pygame.time.get_ticks()
        self.meta_video_last_index = -1
        self.meta_video_surface = None
        if self.meta_video_channel:
            audio = META_VIDEO_DIR / info.get("audio", "")
            if audio.exists():
                try:
                    self.meta_video_channel.stop()
                    self.meta_video_channel.play(pygame.mixer.Sound(str(audio)))
                except pygame.error:
                    pass

    def finish_meta_video(self):
        after = self.meta_video_after
        previous_music = self.meta_video_music_state or {}
        if self.meta_video_channel:
            self.meta_video_channel.stop()
        self.meta_video_name = None
        self.meta_video_after = None
        self.meta_video_tick = 0
        self.meta_video_last_index = -1
        self.meta_video_surface = None
        self.meta_video_music_state = None
        if after == "matrix_menu":
            self.story_overlay = None
            self.mode = "menu"
            self.music.set_phase(-1, force=True)
            self.music.leave_special(restart=True)
        elif after == "porn_confirm":
            self.story_overlay = 200
            self.story200_stage = "porn_confirm"
            self.story200_tick = 0
            self.music.phase = previous_music.get("phase", self.music.phase)
            self.music.enabled = previous_music.get("enabled", self.music.enabled)
            if previous_music.get("paused", False):
                self.music.leave_special(restart=False)
                self.music.paused = True
            else:
                self.music.leave_special(restart=True)
        else:
            self.music.phase = previous_music.get("phase", self.music.phase)
            self.music.enabled = previous_music.get("enabled", self.music.enabled)
            self.music.leave_special(restart=not previous_music.get("paused", False))
            self.music.paused = bool(previous_music.get("paused", False))

    def start_story200_secret(self, action):
        # Codes on the winner-choice screen are alternate endings, NOT the ordinary in-game cheats.
        self.secret_cooldown = 12
        self.secret_buffer = ""
        self.physical_secret_buffer = ""
        if action == "matrix":
            self.begin_meta_video("matrix", "matrix_menu")
            return
        if action == "jetix":
            self.story200_stage = "jetix_thanks"
            self.story200_tick = 0
            return
        if action == "porn_gallery":
            self.begin_meta_video("porn", "porn_confirm")
            return
        if action == "vtd":
            files = [p for p in VTD_DIR.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO] if VTD_DIR.exists() else []
            if files and self.vtd_channel:
                try:
                    self.music.enter_special()
                    self.vtd_current = random.choice(files)
                    snd = pygame.mixer.Sound(str(self.vtd_current))
                    self.vtd_channel.stop(); self.vtd_channel.play(snd, loops=-1)
                    self.vtd_active = True
                    self.vtd_locked = True
                    self.vtd_intro_timer = int(FPS * 0.35)
                except pygame.error:
                    pass
            self.story_winner = "vtd"
            self.guardians_route = False
            self.phobos_route = False
            self.horror_piece_mode = False
            self.story_overlay = None
            return

    def open_random_adult_site(self):
        if not ADULT_SITES_FILE.exists():
            return False
        urls=[]
        for line in ADULT_SITES_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            line=line.strip()
            if line.startswith("http://") or line.startswith("https://"):
                urls.append(line)
        if not urls:
            return False
        try:
            webbrowser.open(random.choice(urls), new=2)
            return True
        except Exception:
            return False

    def draw_meta_video(self):
        info = self.meta_video_manifest.get(self.meta_video_name or "")
        self.canvas.fill((0,0,0))
        if not info:
            return
        fps = float(info.get("fps", 12))
        elapsed = max(0.0, (pygame.time.get_ticks() - getattr(self, "meta_video_started_ms", pygame.time.get_ticks())) / 1000.0)
        # Real-time clock: slow image loading may skip a frame, but never slows the whole movie.
        idx = min(int(elapsed * fps), max(0, int(info.get("frame_count",1))-1))
        if idx != self.meta_video_last_index:
            fp = META_VIDEO_DIR / info.get("frames_dir", "") / f"{idx+1:05d}.jpg"
            if fp.exists():
                try:
                    self.meta_video_surface = pygame.image.load(str(fp)).convert()
                    self.meta_video_last_index = idx
                except pygame.error:
                    pass
        if self.meta_video_surface:
            self.blit_cover(self.meta_video_surface, pygame.Rect(0,0,WINDOW_W,WINDOW_H))
        hint=self.small.render("ESC — SKIP",True,(220,220,225))
        self.canvas.blit(hint,(20,WINDOW_H-40))

    def secret_image_files(self):
        if not PORN_DIR.exists():
            return []
        return [p for p in PORN_DIR.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGES]

    def secret_gameplay_context(self):
        """Secret words are accepted only during live, unobstructed Tetris."""
        return (
            self.mode == "game"
            and self.story_overlay is None
            and not self.phobos_room
            and not self.paused
            and not self.game_over
            and not self.meta_video_name
        )

    def start_secret(self, action):
        if not self.secret_gameplay_context():
            return
        if self.secret_cooldown > 0:
            return
        if self.voice_cooldown > 0: self.voice_cooldown -= 1
        self.secret_cooldown = 12
        self.secret_buffer = ""
        self.physical_secret_buffer = ""
        if action == "porn_gallery":
            files = self.secret_image_files()
            if len(files) > 1 and self.last_secret_image in files:
                files = [f for f in files if f != self.last_secret_image]
            if files:
                chosen = random.choice(files)
                self.last_secret_image = chosen
                try:
                    self.secret_image = pygame.image.load(str(chosen)).convert_alpha()
                except pygame.error:
                    self.secret_image = None
            self.secret_overlay = "porn_gallery"
            self.music.pause()
            if random.randrange(5) == 0:
                self.play_voice("porn", force=True)
        elif action == "ru_18":
            self.secret_overlay = "ru_18"
            self.secret_timer = FPS
        elif action == "matrix":
            self.matrix_timer = FPS * 9
            if random.random() < 0.02:
                self.play_voice("matrix_fan", force=True)
        elif action == "jetix":
            self.jetix_timer = FPS * 6
        elif action == "vtd":
            files = [p for p in VTD_DIR.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO] if VTD_DIR.exists() else []
            if files and self.vtd_channel:
                try:
                    self.music.enter_special()
                    self.vtd_current = random.choice(files)
                    snd = pygame.mixer.Sound(str(self.vtd_current))
                    self.vtd_channel.stop()
                    self.vtd_channel.play(snd)
                    self.vtd_active = True
                    if self.mode == "menu":
                        self.menu_secret_vtd_pending = True
                    self.vtd_intro_timer = int(FPS * 0.35)
                except pygame.error as exc:
                    print(f"[secret music] {exc}")
                    self.music.leave_special(restart=True)

    def skip_music(self):
        if self.vtd_active and self.vtd_channel:
            files = [p for p in VTD_DIR.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO] if VTD_DIR.exists() else []
            if files:
                current = getattr(self, "vtd_current", None)
                choices = [p for p in files if p != current] or files
                self.vtd_current = random.choice(choices)
                try:
                    snd = pygame.mixer.Sound(str(self.vtd_current))
                    self.vtd_channel.stop(); self.vtd_channel.play(snd, loops=-1 if self.music.loop_current else 0)
                except pygame.error: pass
        else:
            self.music.skip()

    def toggle_music_loop(self):
        new_state = not self.music.loop_current
        self.music.loop_current = new_state
        if self.vtd_active and self.vtd_channel and getattr(self, "vtd_current", None):
            try:
                snd = pygame.mixer.Sound(str(self.vtd_current))
                self.vtd_channel.stop()
                self.vtd_channel.play(snd, loops=-1 if new_state else 0)
                if self.voice_channel and self.voice_channel.get_busy():
                    self.vtd_channel.set_volume(0.28)
            except pygame.error:
                pass
        elif self.music.current and self.music.enabled and not self.music.special_lock:
            try:
                pygame.mixer.music.load(str(self.music.current))
                pygame.mixer.music.play(-1 if new_state else 0)
                pygame.mixer.music.set_volume(self.music.base_volume)
            except pygame.error:
                pass
        return new_state

    def exit_special_music(self):
        if self.vtd_locked:
            return
        if self.vtd_active and self.vtd_channel:
            self.vtd_channel.stop()
            self.vtd_active = False
            self.vtd_intro_timer = 0
            self.music.leave_special(restart=True)

    def cancel_secret_effects(self, restart_music=False):
        """Clear every code effect when live Tetris is no longer visible."""
        self.secret_buffer = ""
        self.physical_secret_buffer = ""
        self.secret_overlay = None
        self.secret_image = None
        self.secret_timer = 0
        self.matrix_timer = 0
        self.jetix_timer = 0
        self.vtd_intro_timer = 0
        if self.vtd_channel:
            self.vtd_channel.stop()
        self.vtd_active = False
        self.vtd_locked = False
        if self.music.special_lock:
            self.music.leave_special(restart=restart_music)

    def feed_secret_char(self, ch):
        """Feed layout-aware text into a rolling secret-code buffer.

        Crucially, this never consumes gameplay input. Physical controls are
        handled separately through SDL scancodes, so entering a code cannot
        leave WASD/W/X/Z/C in a broken partial-prefix state.
        """
        if not self.secret_gameplay_context():
            self.secret_buffer = ""
            self.physical_secret_buffer = ""
            return
        if not ch or not ch.isprintable() or ch.isspace():
            return
        for char in ch.lower():
            if not char.isprintable() or char.isspace():
                continue
            self.secret_buffer = (self.secret_buffer + char)[-self.secret_buffer_limit:]
            # Longest codes first in case one code is a suffix of another.
            for code in sorted(self.secret_codes, key=len, reverse=True):
                if self.secret_buffer.endswith(code):
                    self.start_secret(self.secret_codes[code])
                    return

    def feed_physical_secret(self, scancode):
        """Track US-letter physical key positions independent of active layout.

        This makes MATRIX/JETIX/PORN/VTD work even while macOS is set to Russian.
        Russian textual aliases still work through event.unicode in parallel.
        """
        if not self.secret_gameplay_context():
            self.secret_buffer = ""
            self.physical_secret_buffer = ""
            return
        ch = PHYSICAL_LETTERS.get(scancode)
        if not ch:
            return
        self.physical_secret_buffer = (self.physical_secret_buffer + ch)[-self.secret_buffer_limit:]
        physical_codes = {
            "porn": "porn_gallery",
            "matrix": "matrix",
            "jetix": "jetix",
            "vtd": "vtd",
        }
        for code in sorted(physical_codes, key=len, reverse=True):
            if self.physical_secret_buffer.endswith(code):
                self.start_secret(physical_codes[code])
                return

    def developer_add_lines(self, amount=10):
        before = self.lines
        self.lines += amount
        old_phase = 0 if before < LINES_RESISTANCE else 1 if before < LINES_PHASE2 else 2
        if before < LINES_RESISTANCE <= self.lines and 100 not in self.story_seen:
            self.story_seen.add(100)
            self.start_story100()
        elif before < LINES_PHASE2 <= self.lines and 200 not in self.story_seen:
            self.story_seen.add(200)
            self.consecutive_game_overs = 0
            self.story_overlay = 200
            self.story200_stage = "cinematic_reverse"
            self.story200_tick = 0
            self.winner_choice = 0
            self.music.pause()
        elif self.phobos_route and self.lines >= 300 and 300 not in self.story_seen:
            self.enter_phobos_room("developer_lines")
        elif self.phase_index() != old_phase:
            self.music.set_phase(self.phase_index(), force=True)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.cancel_secret_effects(restart_music=True)
            self.music.pause()
            # Pause is a menu state: no Phobos labels or contextual remarks.
            self.pause_voice_pending = None
        else:
            self.pause_voice_pending = None
            if not self.vtd_active:
                self.music.resume()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode(self.display_size, pygame.RESIZABLE)

    def handle_game_over_voice(self):
        if self.game_over_voice_handled:
            return
        if self.empty_roster_bored:
            self.game_over_voice_handled = True
            return
        self.game_over_voice_handled = True
        # 200+ is Free Play after Phobos has already been defeated. He never
        # mocks a completed run, and a victory permanently disables you_loser
        # for the remainder of this app session.
        if self.lines >= LINES_PHASE2 or self.session_has_victory:
            return
        self.consecutive_game_overs += 1
        loser = self.voice_paths.get("you_loser")
        if self.consecutive_game_overs >= 5 and not self.loser_streak_voice_used and loser and loser.exists():
            if self.play_external_voice(loser, force=True):
                self.loser_streak_voice_used = True
                return
        if random.random() < 0.38:
            # failed_last_time.wav is a 145-second editor export accidentally
            # placed among short replies. Keep it archived on disk, but never
            # select it as a Game Over line.
            expected = self.voice_paths.get("expected_no_less")
            if expected and expected.exists():
                self.play_external_voice(expected, force=True)

    def piece_to_character(self, kind):
        return {"I":"cornelia","J":"taranee","L":"haylin","T":"caleb","O":"blunk","S":"irma","Z":"will"}.get(kind)

    def character_to_piece(self, ch):
        return {"cornelia":"I","taranee":"J","haylin":"L","caleb":"T","blunk":"O","irma":"S","will":"Z"}.get(ch)

    def character_exists(self, ch):
        k=self.character_to_piece(ch)
        return bool(k and self.character_enabled.get(k,True))

    def active_intro_characters(self):
        return [ch for ch in self.intro_characters if self.character_exists(ch)]

    def pick_active_character(self, prefer=None):
        active=self.active_intro_characters()
        if prefer and prefer in active: return prefer
        return random.choice(active) if active else None

    def load_settings(self):
        try:
            data=json.loads(SETTINGS_PATH.read_text(encoding="utf-8")) if SETTINGS_PATH.exists() else {}
            chars=data.get("characters",{})
            for k in PIECES: self.character_enabled[k]=bool(chars.get(k,True))
            self.phobos_enabled=bool(data.get("phobos",True))
            self.start_speed=max(1,min(5,int(data.get("start_speed",1))))
            mode=str(data.get("figure_fall_mode","phobos")).lower()
            self.figure_fall_mode=mode if mode in ("phobos","classic") else "phobos"
        except Exception:
            pass

    def save_settings(self):
        try:
            SETTINGS_PATH.write_text(json.dumps({"characters":self.character_enabled,"phobos":self.phobos_enabled,"start_speed":self.start_speed,"figure_fall_mode":self.figure_fall_mode},ensure_ascii=False,indent=2),encoding="utf-8")
        except Exception as exc:
            print("[settings]",exc)

    def settings_root_items(self):
        return ["GAME", "CHARACTERS", "BACK"]

    def settings_game_items(self):
        return ["START SPEED", "ПАДЕНИЕ ФИГУР", "FREE PLAY", "BACK"]

    def figure_fall_label(self):
        return "КЛАССИК" if self.figure_fall_mode == "classic" else "ФОБОС"

    def settings_character_items(self):
        return [(k,self.character_labels[k]) for k in ("I","J","L","T","O","S","Z")]+[("PHOBOS","PHOBOS"),("BACK","BACK") ]

    def settings_items(self):
        if self.settings_page == "root": return self.settings_root_items()
        if self.settings_page == "game": return self.settings_game_items()
        return self.settings_character_items()

    def settings_enter(self):
        items=self.settings_items()
        item=items[self.settings_index]
        if self.settings_page == "root":
            if item == "GAME": self.settings_page="game"; self.settings_index=0; self.settings_message=""
            elif item == "CHARACTERS": self.settings_page="characters"; self.settings_index=0; self.settings_message=""
            else: self.mode="menu"
            return
        if self.settings_page == "game":
            if item == "START SPEED":
                self.start_speed = 1 if self.start_speed >= 5 else self.start_speed + 1
                self.save_settings(); self.settings_message=f"START SPEED: {self.start_speed}"
            elif item == "ПАДЕНИЕ ФИГУР":
                self.figure_fall_mode = "classic" if self.figure_fall_mode == "phobos" else "phobos"
                self.classic_piece_queue = []; self.classic_piece_signature = ()
                self.save_settings(); self.settings_message=f"ПАДЕНИЕ ФИГУР: {self.figure_fall_label()}"
            elif item == "FREE PLAY":
                self.settings_message="ХА-ХА. СВОБОДА НЕДОСТУПНА."
            else:
                self.settings_page="root"; self.settings_index=0; self.settings_message=""
            return
        key,label=item
        if key == "BACK":
            self.settings_page="root"; self.settings_index=0; self.settings_message=""; return
        if key=="PHOBOS": self.phobos_enabled=not self.phobos_enabled
        else: self.character_enabled[key]=not self.character_enabled[key]
        self.save_settings()

    def settings_adjust(self, delta):
        item = self.settings_items()[self.settings_index]
        if self.settings_page == "game" and item == "START SPEED":
            self.start_speed=max(1,min(5,self.start_speed+delta)); self.save_settings(); self.settings_message=f"START SPEED: {self.start_speed}"
        elif self.settings_page == "game" and item == "ПАДЕНИЕ ФИГУР":
            self.figure_fall_mode = "classic" if self.figure_fall_mode == "phobos" else "phobos"
            self.classic_piece_queue = []; self.classic_piece_signature = ()
            self.save_settings(); self.settings_message=f"ПАДЕНИЕ ФИГУР: {self.figure_fall_label()}"
        else:
            self.settings_enter()

    def settings_rects(self):
        items=self.settings_items(); rects=[]
        if self.settings_page == "characters":
            for i in range(len(items)): rects.append(pygame.Rect(150,190+i*70,560,54))
        else:
            for i in range(len(items)): rects.append(pygame.Rect(190,300+i*95,500,66))
        return rects

    def draw_settings(self):
        self.draw_background("menu")
        ov=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); ov.fill((0,0,0,205)); self.canvas.blit(ov,(0,0))
        page_titles={"root":"SETTINGS","game":"SETTINGS — GAME","characters":"SETTINGS — CHARACTERS"}
        title=self.big.render(page_titles[self.settings_page],True,COLORS["accent"]); self.canvas.blit(title,title.get_rect(center=(WINDOW_W//2,90)))
        if self.settings_page == "root":
            sub="Основные параметры игры. Некоторые вещи спрятаны чуть глубже."
        elif self.settings_page == "game":
            sub="Скорость и порядок появления фигур. Режим ФОБОС используется по умолчанию."
        else:
            sub="Удалённый персонаж исчезает из фигур, голосов и сюжетных сцен."
        ss=self.small.render(sub,True,COLORS["text"]); self.canvas.blit(ss,ss.get_rect(center=(WINDOW_W//2,150)))
        rects=self.settings_rects(); items=self.settings_items()
        for i,item in enumerate(items):
            r=rects[i]
            if i==self.settings_index: pygame.draw.rect(self.canvas,(82,42,105),r)
            pygame.draw.rect(self.canvas,(120,85,140),r,2)
            if self.settings_page == "characters":
                key,label=item
                if key=="BACK": text="BACK"; state=""
                else:
                    enabled=self.phobos_enabled if key=="PHOBOS" else self.character_enabled.get(key,True)
                    text=label; state="ACTIVE" if enabled else "DELETED"
                self.text(("▶ " if i==self.settings_index else "  ")+text,r.x+18,r.y+12,self.font)
                if state: self.text(state,r.right-175,r.y+15,self.small,(130,240,160) if state=="ACTIVE" else (245,90,105))
            else:
                text=item
                if self.settings_page=="game" and item=="START SPEED": text=f"START SPEED   {self.start_speed}"
                if self.settings_page=="game" and item=="ПАДЕНИЕ ФИГУР": text=f"ПАДЕНИЕ ФИГУР   {self.figure_fall_label()}"
                if self.settings_page=="game" and item=="FREE PLAY": text="FREE PLAY   [LOCKED]"
                tx=self.font.render(("▶ " if i==self.settings_index else "  ")+text,True,COLORS["text"]); self.canvas.blit(tx,tx.get_rect(center=r.center))
        if self.settings_message:
            msg=self.font.render(self.settings_message,True,(235,150,245)); self.canvas.blit(msg,msg.get_rect(center=(WINDOW_W//2,850)))
        hint=self.small.render("↑ ↓ / mouse — select    ENTER / click — open    ESC — back",True,(185,175,195)); self.canvas.blit(hint,hint.get_rect(center=(WINDOW_W//2,1010)))

    def read_records(self):
        try:
            data = json.loads(RECORDS_PATH.read_text(encoding="utf-8")) if RECORDS_PATH.exists() else []
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def save_record(self):
        if getattr(self, "record_saved", False):
            return
        self.record_saved = True
        data = self.read_records()
        data.append({"lines": int(self.lines), "score": int(self.score)})
        data = sorted(data, key=lambda r: (r.get("lines", 0), r.get("score", 0)), reverse=True)[:10]
        try:
            RECORDS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[records] {exc}")

    def start_new_game(self):
        if self.sprites is None:
            self.sprites = SpriteSet()
        carry_vtd = bool(getattr(self, "vtd_active", False) or getattr(self, "menu_secret_vtd_pending", False))
        self.reset()
        self.mode = "game"
        if not self.phobos_enabled:
            self.phobos_deleted_win = True
            self.music.stop()
            return
        self.music.resume()
        if carry_vtd:
            self.menu_secret_vtd_pending = False
            self.start_secret("vtd")
        if random.random() < 0.65:
            start_pool = ["start", "dark", "lets_begin", "your_power_is_nothing", "last_hope_universe", "new_era_phobos"]
            start_weights = [25, 25, 24, 9, 8, 9]
            self.play_voice(random.choices(start_pool, weights=start_weights, k=1)[0], force=True)

    def window_to_canvas(self, pos):
        ww, wh = self.window.get_size()
        scale = min(ww / WINDOW_W, wh / WINDOW_H)
        sw, sh = WINDOW_W * scale, WINDOW_H * scale
        ox, oy = (ww - sw) / 2, (wh - sh) / 2
        x, y = pos
        if x < ox or y < oy or x >= ox + sw or y >= oy + sh:
            return None
        return ((x - ox) / scale, (y - oy) / scale)

    def menu_rects(self):
        return [pygame.Rect(88, 388 + i * 72, 330, 55) for i in range(len(self.menu_items))]

    def pause_rects(self):
        out = []
        for i in range(len(self.pause_menu_items)):
            y = WINDOW_H // 2 - 45 + i * 75
            out.append(pygame.Rect(WINDOW_W // 2 - 190, y - 10, 380, 55))
        return out

    def game_over_rects(self):
        return [pygame.Rect(WINDOW_W // 2 - 180, WINDOW_H // 2 + 60 + i * 70, 360, 52) for i in range(2)]

    def handle_mouse_motion(self, pos):
        p = self.window_to_canvas(pos)
        if p is None:
            return
        if self.mode == "game" and self.story_overlay == 100:
            if self.story100_stage == "wait_key":
                self.story100_stage = "after_key"
                self.story100_tick = 0
                self.story100_sfx_played.clear()
            return
        if self.mode == "game" and self.story_overlay == 200 and self.story200_stage == "choice":
            box_w, gap=310,36; start_x=(WINDOW_W-(box_w*2+gap))//2
            for i in range(2):
                if pygame.Rect(start_x+i*(box_w+gap),420,box_w,100).collidepoint(p): self.winner_choice=i; return
        if self.mode == "settings":
            for i, rect in enumerate(self.settings_rects()):
                if rect.collidepoint(p):
                    self.settings_index=i
                    return
        if self.mode == "collection":
            for i, rect in enumerate(self.collection_rects()):
                if rect.collidepoint(p): self.collection_item_index=i; return
        if self.mode == "minigame":
            if self.mg_over:
                return
            # Mouse remains usable where horizontal movement is meaningful; gameplay never relies on it.
            if self.minigame in ("HEART BREAKER","TARANEE FIRE SHOT","CORNELIA EARTH GARDEN","BLUNK WASHING","IRMA BUBBLE TROUBLE"):
                self.mg_player[0]=max(85,min(WINDOW_W-85,p[0]))
                if self.minigame=="HEART BREAKER": self.mg_paddle_x=self.mg_player[0]
            return
        if self.mode == "menu":
            for i, rect in enumerate(self.menu_rects()):
                if rect.collidepoint(p):
                    if self.menu_index != i:
                        self.menu_index = i
                        self.menu_voice_pending = i
                        self.menu_voice_delay = int(FPS * 0.45)
                    return
        elif self.mode == "game" and self.paused:
            for i, rect in enumerate(self.pause_rects()):
                if rect.collidepoint(p):
                    if self.pause_menu_index != i:
                        self.pause_menu_index = i
                        self.pause_voice_pending = i
                        self.pause_voice_delay = int(FPS * 0.35)
                    return
        elif self.mode == "game" and self.game_over:
            for i, rect in enumerate(self.game_over_rects()):
                if rect.collidepoint(p):
                    self.game_over_index = i
                    return

    def handle_mouse_click(self, pos, button=1):
        if button != 1:
            return
        p = self.window_to_canvas(pos)
        if p is None:
            return
        if self.mode == "game" and self.story_overlay == 200 and self.story200_stage == "choice":
            box_w, gap=310,36; start_x=(WINDOW_W-(box_w*2+gap))//2
            for i in range(2):
                if pygame.Rect(start_x+i*(box_w+gap),420,box_w,100).collidepoint(p): self.winner_choice=i; self.choose_story_winner(); return
        if self.mode == "splash":
            self.mode = "menu"
            return
        if self.mode == "records":
            self.mode = "menu"
            return
        if self.mode == "settings":
            for i, rect in enumerate(self.settings_rects()):
                if rect.collidepoint(p):
                    self.settings_index=i
                    self.settings_enter()
                    return
        if self.mode == "collection":
            for i, rect in enumerate(self.collection_rects()):
                if rect.collidepoint(p): self.collection_item_index=i; self.collection_activate(); return
        if self.mode == "minigame":
            if self.mg_over:
                retry=pygame.Rect(300,565,400,42); back=pygame.Rect(300,610,400,42)
                if retry.collidepoint(p): self.start_minigame(self.minigame)
                elif back.collidepoint(p): self.leave_minigame()
                return
            if self.minigame in ("HEART BREAKER","TARANEE FIRE SHOT","CORNELIA EARTH GARDEN","BLUNK WASHING","IRMA BUBBLE TROUBLE"):
                self.mg_player[0]=max(85,min(WINDOW_W-85,p[0]))
                if self.minigame=="HEART BREAKER": self.mg_paddle_x=self.mg_player[0]
            # Clicking performs the primary action where there is one.
            if self.minigame in ("HAY LIN FLIGHT","TARANEE FIRE SHOT","CORNELIA EARTH GARDEN","IRMA BUBBLE TROUBLE","IRMA WHIRLPOOL","PHOBOS TETRIS ???"):
                self.handle_minigame_key(pygame.K_SPACE)
            return
        if self.mode == "menu":
            for i, rect in enumerate(self.menu_rects()):
                if rect.collidepoint(p):
                    self.menu_index = i
                    item = self.menu_items[i]
                    if item == "NEW GAME": self.start_new_game()
                    elif item == "RECORDS": self.mode = "records"
                    elif item == "SETTINGS": self.mode = "settings"; self.settings_page="root"; self.settings_index=0; self.settings_message=""
                    elif item == "COLLECTION": self.open_collection()
                    else: self.running = False
                    return
        if self.mode == "game" and self.paused:
            for i, rect in enumerate(self.pause_rects()):
                if rect.collidepoint(p):
                    self.pause_menu_index = i
                    item = self.pause_menu_items[i]
                    if item == "CONTINUE": self.toggle_pause()
                    elif item == "RESTART": self.start_new_game()
                    else:
                        self.paused = False; self.mode = "menu"; self.music.stop()
                    return
        if self.mode == "game" and self.game_over:
            for i, rect in enumerate(self.game_over_rects()):
                if rect.collidepoint(p):
                    self.game_over_index = i
                    if i == 0: self.start_new_game()
                    else:
                        self.mode = "menu"; self.music.stop(); self.game_over = False
                    return

    def handle_menu_key(self, key, scancode=None):
        if self.mode == "splash":
            if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self.mode = "menu"; self.music.set_phase(-1, force=True)
            return True
        if self.mode == "records":
            if key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN): self.mode = "menu"
            return True
        if self.mode == "settings":
            if key == pygame.K_UP: self.settings_index=(self.settings_index-1)%len(self.settings_items())
            elif key == pygame.K_DOWN: self.settings_index=(self.settings_index+1)%len(self.settings_items())
            elif key in (pygame.K_SPACE,pygame.K_RETURN): self.settings_enter()
            elif key == pygame.K_LEFT: self.settings_adjust(-1)
            elif key == pygame.K_RIGHT: self.settings_adjust(1)
            elif key == pygame.K_ESCAPE:
                if self.settings_page == "root": self.mode="menu"
                else: self.settings_page="root"; self.settings_index=0; self.settings_message=""
            return True
        if self.mode == "collection":
            self.handle_collection_key(key)
            return True
        if self.mode == "minigame":
            self.handle_minigame_key(key)
            return True
        if self.mode != "menu":
            return False
        if key == pygame.K_UP or scancode == SC_W:
            self.menu_index = (self.menu_index - 1) % len(self.menu_items)
            self.menu_voice_pending = self.menu_index; self.menu_voice_delay = int(FPS * 0.25)
        elif key == pygame.K_DOWN or scancode == SC_S:
            self.menu_index = (self.menu_index + 1) % len(self.menu_items)
            self.menu_voice_pending = self.menu_index; self.menu_voice_delay = int(FPS * 0.25)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            item = self.menu_items[self.menu_index]
            if item == "NEW GAME":
                self.start_new_game()
            elif item == "RECORDS": self.mode = "records"
            elif item == "SETTINGS": self.mode = "settings"; self.settings_page="root"; self.settings_index=0; self.settings_message=""
            elif item == "COLLECTION": self.open_collection()
            else: self.running = False
        elif key == pygame.K_ESCAPE:
            self.running = False
        return True

    def handle_keydown(self, key, unicode_char="", mod=0, scancode=None):
        if scancode is not None:
            self.held_scancodes.add(scancode)
        if not self.secret_gameplay_context():
            self.secret_buffer = ""
            self.physical_secret_buffer = ""

        if self.phobos_deleted_win:
            self.phobos_deleted_win=False; self.mode="menu"; self.music.set_phase(-1,force=True); return

        if key == pygame.K_F11 or (key in (pygame.K_RETURN, pygame.K_KP_ENTER) and (mod & (pygame.KMOD_META | pygame.KMOD_ALT))):
            self.toggle_fullscreen(); return

        if self.meta_video_name:
            if key == pygame.K_ESCAPE:
                self.finish_meta_video()
            return

        if self.mode == "intro":
            if key in (pygame.K_ESCAPE, pygame.K_x) or scancode == SC_X:
                self.finish_intro()
            elif key in (pygame.K_SPACE, pygame.K_RETURN):
                # SPACE: first completes the current typewriter line, then advances.
                line = self.current_intro_dialogue_line()
                if line and self.intro_scene_tick < len(line) * 3:
                    self.intro_scene_tick = len(line) * 3
                else:
                    self.advance_intro()
            return

        # The Phobos room is outside the normal game. Handle its local key
        # reactions before the global secret-code buffers, so MATRIX, PORN,
        # JETIX, VTD and their Russian aliases cannot activate here.
        if self.story_overlay == 300:
            self.react_phobos_room_key(key, unicode_char, mod, scancode)
            return

        # Secret words belong only to live Tetris. Menus, pause, Game Over,
        # minigames and every cutscene clear partial input instead of carrying
        # it into the next gameplay frame.
        secret_input = self.secret_gameplay_context()
        if not secret_input:
            self.secret_buffer = ""
            self.physical_secret_buffer = ""
        if secret_input and unicode_char and unicode_char.isalpha():
            layout = "ru" if ("а" <= unicode_char.lower() <= "я" or unicode_char.lower() == "ё") else "latin"
            if self.last_layout and layout != self.last_layout and not self.layout_reaction_done and random.random() < 0.08:
                if self.play_voice("layout"):
                    self.layout_reaction_done = True
            self.last_layout = layout
        if secret_input and scancode is not None:
            self.feed_physical_secret(scancode)
        if secret_input and unicode_char:
            self.feed_secret_char(unicode_char)

        if self.secret_overlay == "porn_gallery":
            if key == pygame.K_SPACE:
                self.secret_overlay = None
                self.secret_image = None
                if not self.vtd_active:
                    self.music.resume()
            return

        if self.handle_menu_key(key, scancode):
            return
        if self.phobos_deleted_win:
            self.phobos_deleted_win=False; self.mode="menu"; self.music.set_phase(-1,force=True); return
        if self.story_overlay is not None:
            if self.story_overlay == 100:
                # X skips the whole second cutscene. SPACE advances the current beat.
                if key in (pygame.K_x, pygame.K_ESCAPE) or scancode == SC_X:
                    self.finish_story100()
                    return
                if self.story100_stage == "wait_key":
                    self.story100_stage = "after_key"
                    self.story100_tick = 0
                    self.story100_sfx_played.clear()
                elif key in (pygame.K_SPACE, pygame.K_RETURN):
                    order = ["glitch", "blackout", "terminal", "wait_key", "after_key", "hall", "guardian", "phobos", "title"]
                    if self.story100_stage == "title":
                        self.finish_story100()
                    else:
                        try:
                            self.story100_stage = order[min(order.index(self.story100_stage)+1, len(order)-1)]
                            self.story100_tick = 0
                            self.story100_sfx_played.clear()
                        except ValueError:
                            pass
                return
            if self.story_overlay == 200:
                cinematic_order=["cinematic_reverse","cinematic_heart","cinematic_phobos","cinematic_break","choice"]
                if key in (pygame.K_x, pygame.K_ESCAPE) or scancode == SC_X:
                    if self.collection_cutscene:
                        self.story_overlay=None; self.collection_cutscene=False; self.mode="collection"; self.collection_page="CUTSCENES"; self.collection_item_index=0; self.music.set_phase(-1,force=True)
                    else:
                        self.story200_stage="choice"; self.story200_tick=0
                    return
                if self.story200_stage in cinematic_order[:-1]:
                    if key in (pygame.K_SPACE,pygame.K_RETURN):
                        i=cinematic_order.index(self.story200_stage); self.story200_stage=cinematic_order[i+1]; self.story200_tick=0
                    return
                if self.story200_stage == "choice":
                    if key in (pygame.K_LEFT, pygame.K_a): self.winner_choice = 0
                    elif key in (pygame.K_RIGHT, pygame.K_d): self.winner_choice = 1
                    elif key in (pygame.K_SPACE, pygame.K_RETURN): self.choose_story_winner()
                elif self.story200_stage == "jetix_thanks":
                    if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                        self.story200_stage = "choice"; self.story200_tick = 0
                elif self.story200_stage == "porn_confirm":
                    if key == pygame.K_y:
                        self.open_random_adult_site()
                        self.story200_stage = "choice"; self.story200_tick = 0
                    elif key in (pygame.K_n, pygame.K_ESCAPE):
                        self.story200_stage = "choice"; self.story200_tick = 0
                elif key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.continue_after_story200()
                return
            if key == pygame.K_SPACE:
                self.story_overlay = None
                if not self.vtd_active:
                    self.music.resume()
            return
        if self.game_over:
            self.save_record()
            self.handle_game_over_voice()
            if key == pygame.K_UP or scancode == SC_W:
                self.game_over_index = (self.game_over_index - 1) % len(self.game_over_items)
            elif key == pygame.K_DOWN or scancode == SC_S:
                self.game_over_index = (self.game_over_index + 1) % len(self.game_over_items)
            elif key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.game_over_index == 0:
                    self.start_new_game()
                else:
                    self.mode = "menu"; self.music.stop(); self.game_over = False
            elif key in (pygame.K_ESCAPE, pygame.K_m):
                self.mode = "menu"; self.music.stop(); self.game_over = False
            return

        if self.paused:
            if key == pygame.K_UP or scancode == SC_W:
                self.pause_menu_index = (self.pause_menu_index - 1) % len(self.pause_menu_items)
                self.pause_voice_pending = self.pause_menu_index; self.pause_voice_delay = int(FPS * 0.20); return
            if key == pygame.K_DOWN or scancode == SC_S:
                self.pause_menu_index = (self.pause_menu_index + 1) % len(self.pause_menu_items)
                self.pause_voice_pending = self.pause_menu_index; self.pause_voice_delay = int(FPS * 0.20); return
            if key in (pygame.K_RETURN,):
                item = self.pause_menu_items[self.pause_menu_index]
                if item == "CONTINUE": self.toggle_pause()
                elif item == "RESTART": self.start_new_game()
                else: self.paused=False; self.mode="menu"; self.music.stop()
                return
            if key == pygame.K_SPACE:
                self.toggle_pause(); return
            if key == pygame.K_ESCAPE:
                self.paused=False; self.mode="menu"; self.music.stop(); return
            return

        # Music controls use rare symbols so they never collide with secret words.
        # NEXT accepts Ё on RU layouts plus common `~\| variants used by Mac/Windows layouts.
        if unicode_char in ("ё", "Ё", "`", "~", "\\", "|"):
            self.skip_music(); return
        if unicode_char in ("ъ", "Ъ", "]", "}"):
            self.toggle_music_loop(); return
        if unicode_char == "?":
            self.exit_special_music(); return

        if key == pygame.K_SPACE:
            self.toggle_pause(); return
        if key == pygame.K_ESCAPE:
            if self.paused:
                self.toggle_pause()
            else:
                self.toggle_pause()
            return
        if scancode == SC_M or key == pygame.K_m:
            self.music.toggle(); return
        if (scancode == SC_Q or key == pygame.K_q) and (mod & pygame.KMOD_SHIFT):
            self.developer_add_lines(10); return
        if self.paused:
            return

        if key == pygame.K_LEFT or scancode == SC_A:
            self.move(-1, 0)
        elif key == pygame.K_RIGHT or scancode == SC_D:
            self.move(1, 0)
        elif key == pygame.K_UP:
            self.hard_drop()
        elif scancode in (SC_W, SC_X, SC_Z):
            self.rotate()
        elif scancode in (SC_C, SC_LSHIFT, SC_RSHIFT) or key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
            self.hold()

    def update(self):
        self.menu_tick += 1
        if not self.secret_gameplay_context() and (
            self.secret_overlay is not None or self.matrix_timer > 0
            or self.jetix_timer > 0 or self.vtd_active
        ):
            self.cancel_secret_effects(restart_music=False)
        if self.mode == "minigame":
            self.update_minigame()
            return
        if self.meta_video_name:
            self.meta_video_tick += 1
            info = self.meta_video_manifest.get(self.meta_video_name, {})
            elapsed = (pygame.time.get_ticks() - getattr(self, "meta_video_started_ms", pygame.time.get_ticks())) / 1000.0
            if elapsed >= float(info.get("duration", 0.0)):
                self.finish_meta_video()
            return
        if self.mode == "intro":
            self.intro_tick += 1; self.intro_scene_tick += 1
            # v6.16: slightly faster typewriter and automatic continuation after a readable pause.
            line = self.current_intro_dialogue_line()
            if line:
                typed_at = len(line) * 3
                hold_after = max(120, min(190, 95 + len(line)))
                # Never cut off the real Phobos audio in the aftermath scene.
                voice_busy = (self.intro_scene == 6 and self.intro_voice_channel and self.intro_voice_channel.get_busy())
                if self.intro_scene_tick > typed_at + hold_after and not voice_busy:
                    self.advance_intro()
            else:
                durations = (150, 150, 150, 150, 105, 185, 150, 110)
                limit = durations[min(self.intro_scene, len(durations)-1)]
                if self.intro_scene_tick > limit:
                    self.advance_intro()
            return
        # Main-menu navigation intentionally has no Phobos voice-over.
        self.menu_voice_pending = None
        if self.mode != "game":
            # Effects cannot start or remain active outside live Tetris.
            if self.secret_cooldown > 0: self.secret_cooldown -= 1
            if self.secret_timer > 0:
                self.secret_timer -= 1
                if self.secret_timer == 0 and self.secret_overlay == "ru_18": self.secret_overlay = None
            if self.matrix_timer > 0: self.matrix_timer -= 1
            if self.vtd_intro_timer > 0: self.vtd_intro_timer -= 1
            if self.jetix_timer > 0: self.jetix_timer -= 1
            if self.vtd_active and self.vtd_channel and not self.vtd_channel.get_busy() and not self.vtd_locked:
                self.vtd_active = False
                self.vtd_intro_timer = 0
                self.music.leave_special(restart=True)
            if self.mode in ("menu","records","settings","collection") and not self.vtd_active and not self.collection_audio_item:
                self.music.update()
            return
        # Pause-menu navigation is silent as well.
        self.pause_voice_pending = None
        if self.voice_cooldown > 0: self.voice_cooldown -= 1
        if self.secret_cooldown > 0:
            self.secret_cooldown -= 1
        if self.secret_timer > 0:
            self.secret_timer -= 1
            if self.secret_timer == 0 and self.secret_overlay == "ru_18":
                self.secret_overlay = None
        if self.matrix_timer > 0: self.matrix_timer -= 1
        if self.vtd_intro_timer > 0: self.vtd_intro_timer -= 1
        if self.jetix_timer > 0: self.jetix_timer -= 1
        if self.voice_channel and not self.voice_channel.get_busy():
            if self.queued_voice is not None:
                if self.queued_voice_delay > 0:
                    self.queued_voice_delay -= 1
                else:
                    q = self.queued_voice; self.queued_voice = None
                    self.play_external_voice(q, force=True)
            else:
                self.music.duck(False)
                if self.vtd_channel: self.vtd_channel.set_volume(1.0)
        if self.vtd_active and self.vtd_channel and not self.vtd_channel.get_busy() and not self.vtd_locked:
            self.vtd_active = False
            self.vtd_intro_timer = 0
            self.music.leave_special(restart=True)
        # Choosing Phobos makes defeat part of his ending: there is no normal
        # retry menu. The loss tears open the same fourth-wall room at once.
        if self.game_over and self.phobos_route and self.story_winner == "phobos":
            self.enter_phobos_room("phobos_defeat")
            return
        if self.game_over:
            self.save_record()
            self.handle_game_over_voice()
        if self.story_overlay == 100:
            self.update_story100()
            return
        if self.story_overlay == 200:
            self.story200_tick += 1
            auto={"cinematic_reverse":int(FPS*3.2),"cinematic_heart":int(FPS*3.0),"cinematic_phobos":int(FPS*3.0),"cinematic_break":int(FPS*3.0)}
            if self.story200_stage in auto and self.story200_tick >= auto[self.story200_stage]:
                if self.collection_cutscene and self.story200_stage=="cinematic_break":
                    self.story_overlay=None; self.collection_cutscene=False; self.mode="collection"; self.collection_page="CUTSCENES"; self.collection_item_index=0; self.music.set_phase(-1,force=True); return
                order=["cinematic_reverse","cinematic_heart","cinematic_phobos","cinematic_break","choice"]
                self.story200_stage=order[order.index(self.story200_stage)+1]; self.story200_tick=0
                return
            # Before the Phobos 20% vanilla branch, visibly split the Guardians out
            # of their character sprites. The transition is automatic.
            if self.story200_stage == "phobos_split" and self.story200_tick >= FPS * 3:
                self.story200_stage = "phobos_win"
                self.story200_tick = 0
            return
        if self.story_overlay == 300:
            self.phobos_room_tick += 1
            if self.phobos_room_stage == "crash":
                if self.phobos_room_tick >= int(FPS * 1.6):
                    self.phobos_room_stage = "blackout"
                    self.phobos_room_tick = 0
                return
            if self.phobos_room_stage == "blackout":
                if self.phobos_room_tick >= int(FPS * 1.0):
                    self.phobos_room_stage = "room"
                    self.phobos_room_tick = 0
                    # First random text chain after a short silence. No voice in this room.
                    self.phobos_room_next_ms = pygame.time.get_ticks() + 900
                    self.phobos_room_intro_pending = True
                return
            if self.phobos_room_stage == "room":
                now=pygame.time.get_ticks()
                if getattr(self, "phobos_room_intro_pending", False):
                    self.phobos_room_intro_pending=False
                    self.phobos_room_chain={"id":"room_intro","lines":["Ну вот. Я всё испортил, как и обещал.","Играть мне надоело.","Можем просто посидеть здесь немного. Если хочешь — поговорим."]}
                    self.phobos_room_line=0; self.phobos_room_type_started_ms=now; self.phobos_room_type_complete=False; self.phobos_room_next_ms=10**12
                    room_track=ASSET_DIR/"audio"/"music"/"phobos_room"/"PhobosthemeDark.mp3"
                    if room_track.exists() and pygame.mixer.get_init():
                        try: pygame.mixer.music.stop(); pygame.mixer.music.load(str(room_track)); pygame.mixer.music.play(-1); pygame.mixer.music.set_volume(.68)
                        except pygame.error: pass
                if self.phobos_room_chain and not self.phobos_room_type_complete and self.phobos_type_sound and self.phobos_room_tick % 3 == 0:
                    try: self.phobos_type_sound.play()
                    except pygame.error: pass
                if self.phobos_room_wait_until and now >= self.phobos_room_wait_until:
                    self.phobos_room_wait_until=0
                    self.advance_phobos_room_line()
                    self.phobos_room_next_ms = now + 40000
                if not self.phobos_room_wait_until and now >= self.phobos_room_next_ms:
                    self.choose_phobos_room_chain()
            return
        # Empty world easter egg: with every playable character deleted the well remains empty.
        # Test-build timeout is 30 seconds; final release target is 20 minutes.
        if self.current is None and not any(self.character_enabled.values()) and self.story_overlay is None and not self.game_over:
            now=pygame.time.get_ticks()
            if self.empty_roster_started_ms is None: self.empty_roster_started_ms=now
            if not self.empty_roster_bored and now-self.empty_roster_started_ms >= 30000:
                self.empty_roster_bored=True
                self.empty_roster_bored_at=now
                self.music.pause()
                return
            if self.empty_roster_bored and self.empty_roster_bored_at is not None and now-self.empty_roster_bored_at >= 2600:
                self.game_over=True
                return

        # Robust 300-line trigger: entering or already being beyond 300 on the Phobos route
        # must open the fourth-wall room exactly once, including developer line jumps.
        if self.phobos_route and self.lines >= 300 and 300 not in self.story_seen:
            self.enter_phobos_room("lines")
            return
        if self.paused or self.game_over or self.story_overlay is not None or self.secret_overlay == "porn_gallery":
            return
        if self.pending_clear:
            self.pending_clear["frames"] -= 1
            if self.pending_clear["frames"] <= 0:
                self.resolve_pending_clear()
            return
        if not self.vtd_active:
            self.music.update()
        self.play_frames += 1
        if self.play_frames >= self.pause_hint_eligible_at and not self.pause_hint_played:
            # Once eligible, only a small chance each 10 seconds; may never fire this game.
            if self.play_frames % (FPS * 10) == 0 and random.random() < 0.18:
                self.pause_hint_played = True
                self.play_voice("pause_hint")
        if self.current is None:
            return
        self.frame_counter += 1
        keys = pygame.key.get_pressed()
        interval = SOFT_DROP_FRAMES if (keys[pygame.K_DOWN] or SC_S in self.held_scancodes) else self.fall_interval()
        if self.frame_counter >= interval:
            self.frame_counter = 0
            if not self.move(0, 1):
                self.lock_piece()

    def vtd_tint(self, surface):
        if surface is None or not self.vtd_active:
            return surface
        out = surface.copy()
        # Preserve sprite detail while forcing the whole result into a green Matrix palette.
        shade = pygame.Surface(out.get_size(), pygame.SRCALPHA)
        shade.fill((65, 255, 105, 255))
        out.blit(shade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return out

    def draw_board(self):
        panel = pygame.Surface((BOARD_W*CELL, BOARD_H*CELL), pygame.SRCALPHA)
        panel.fill((0, 8, 2, 245) if self.vtd_active else (12, 14, 24, 218))
        self.canvas.blit(panel, (BOARD_X, BOARD_Y))
        grid_col = (18, 90, 35) if self.vtd_active else COLORS["grid"]
        for y in range(BOARD_H):
            for x in range(BOARD_W):
                r = pygame.Rect(BOARD_X+x*CELL, BOARD_Y+y*CELL, CELL, CELL)
                cell = self.board[y][x]
                if cell is not None:
                    if cell.get("plain") and not self.vtd_active:
                        self.draw_plain_cell(r, cell.get("kind", "T"))
                    elif cell["surface"] is not None:
                        self.canvas.blit(self.vtd_tint(cell["surface"]), r.topleft)
                    else:
                        pygame.draw.rect(self.canvas, (45,255,90) if self.vtd_active else COLORS["accent"], r)
                pygame.draw.rect(self.canvas, grid_col, r, 1)
        if not self.pending_clear and self.current is not None:
            if self.vtd_active:
                img = self.sprites.piece_image(self.current["kind"], self.current["rot"], self.phase_index(), horror=self.horror_piece_mode and self.phobos_route)
                if img is not None:
                    self.canvas.blit(self.vtd_tint(img), (BOARD_X+self.current["x"]*CELL, BOARD_Y+self.current["y"]*CELL))
                else:
                    self.sprites.draw_piece(self.canvas, self.current["kind"], self.current["rot"], self.current["x"], self.current["y"], self.phase_index(), horror=self.horror_piece_mode and self.phobos_route)
            else:
                if self.plain_piece_mode():
                    self.draw_plain_piece(self.current["kind"], self.current["rot"], self.current["x"], self.current["y"])
                else:
                    self.sprites.draw_piece(self.canvas, self.current["kind"], self.current["rot"], self.current["x"], self.current["y"], self.phase_index(), horror=self.horror_piece_mode and self.phobos_route)
        else:
            self.draw_clear_effect()

    def draw_clear_effect(self):
        pc = self.pending_clear
        if not pc: return
        rows = pc["rows"]; t = 1.0 - pc["frames"] / max(1, pc["total"])
        if self.phobos_route:
            # Dark-purple lightning for every clear in Phobos's victory route.
            for y in rows:
                cy=BOARD_Y+y*CELL+CELL//2
                for strand in range(3):
                    pts=[(BOARD_X,cy+random.randint(-8,8))]
                    for i in range(1,12):
                        pts.append((BOARD_X+i*(BOARD_W*CELL)//12,cy+random.randint(-18,18)))
                    pts.append((BOARD_X+BOARD_W*CELL,cy+random.randint(-8,8)))
                    pygame.draw.lines(self.canvas,(95,20,150),False,pts,8 if strand==0 else 4)
                    pygame.draw.lines(self.canvas,(190,80,255),False,pts,2)
            if len(rows)==4:
                # Phobos portrait replaces the Heart of Kandrakar.
                source = self.phobos_room_emotions[0] if self.phobos_room_emotions else self.phobos_body
                if source:
                    pulse=0.75+0.18*math.sin(min(1.0,t)*math.pi)
                    h=int(330*pulse); w=max(1,int(source.get_width()*h/source.get_height()))
                    img=pygame.transform.scale(source,(w,h)); img.set_alpha(int(255*(1-max(0,t-0.72)/0.28)))
                    self.canvas.blit(img,img.get_rect(center=(BOARD_X+BOARD_W*CELL//2, BOARD_Y+BOARD_H*CELL//2)))
            return
        if len(rows) < 4:
            # Jagged white/purple lightning across each clearing row.
            for y in rows:
                cy = BOARD_Y + y * CELL + CELL // 2
                pts = [(BOARD_X, cy)]
                for i in range(1, 10):
                    pts.append((BOARD_X + i * (BOARD_W*CELL)//10, cy + random.randint(-10, 10)))
                pts.append((BOARD_X + BOARD_W*CELL, cy))
                pygame.draw.lines(self.canvas, (245,235,255), False, pts, 5)
                pygame.draw.lines(self.canvas, (190,110,255), False, pts, 2)
        else:
            # Heart of Kandrakar: quick center pulse + pink wave.
            cx = BOARD_X + BOARD_W*CELL//2
            cy = BOARD_Y + int((min(rows) + max(rows) + 1) * CELL / 2)
            pulse = math.sin(min(1.0,t)*math.pi)
            radius = int(30 + 230*t)
            glow = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255,80,210,int(90*(1-t))), (cx,cy), radius, max(3,int(18*(1-t))))
            self.canvas.blit(glow,(0,0))
            if self.heart_image:
                scale = 0.55 + 0.25*pulse
                h = int(190*scale); w = max(1,int(self.heart_image.get_width()*h/self.heart_image.get_height()))
                img = pygame.transform.scale(self.heart_image,(w,h))
                img.set_alpha(int(255*(1-max(0,t-0.65)/0.35)))
                self.canvas.blit(img,(cx-w//2,cy-h//2))
            for y in rows:
                r=pygame.Rect(BOARD_X,BOARD_Y+y*CELL,BOARD_W*CELL,CELL)
                flash=pygame.Surface(r.size,pygame.SRCALPHA); flash.fill((255,90,220,int(150*pulse)))
                self.canvas.blit(flash,r.topleft)

    def draw_mini_piece(self, kind, x, y, box_w=240, box_h=170):
        if kind is None:
            return
        shape = SHAPES[kind][0]
        w, h = bbox(shape)
        mini = 28
        if self.plain_piece_mode() and not self.vtd_active:
            ox = x + (box_w - w*mini)//2
            oy = y + (box_h - h*mini)//2
            for dx,dy in shape:
                rr = pygame.Rect(ox+dx*mini, oy+dy*mini, mini, mini)
                self.draw_plain_cell(rr, kind, inset=1)
            return
        img = self.sprites.piece_image(kind, 0, self.phase_index(), horror=self.horror_piece_mode and self.phobos_route)
        if img is None:
            return
        scaled = pygame.transform.scale(self.vtd_tint(img), (w*mini, h*mini))
        px = x + (box_w - w*mini)//2
        py = y + (box_h - h*mini)//2
        self.canvas.blit(scaled, (px, py))

    def text(self, s, x, y, font=None, color=None):
        surf = (font or self.font).render(str(s), True, color or COLORS["text"])
        self.canvas.blit(surf, (x, y))

    def draw_hud(self):
        x = BOARD_X + BOARD_W*CELL + 28
        hud_panel = pygame.Surface((HUD_W-20, WINDOW_H-40), pygame.SRCALPHA)
        hud_panel.fill((8, 8, 16, 205))
        self.canvas.blit(hud_panel, (BOARD_X + BOARD_W*CELL + 18, 20))
        self.text("W.I.T.C.H. TETRIS", x, 30, self.font, COLORS["accent"])
        self.text(f"LINES  {self.lines}", x, 80)
        self.text(f"SCORE  {self.score}", x, 118)
        self.text(f"SPEED  {self.fall_interval()}f", x, 156)
        if self.lines >= LINES_PHASE2 and self.phobos_route:
            phase = "PHOBOS ENDING 200+"
        elif self.lines >= LINES_PHASE2 and self.guardians_route:
            phase = "GUARDIANS 200+"
        else:
            phase = ["PHOBOS 0-99", "RESISTANCE 100-199", "GUARDIANS 200+"][self.phase_index()]
        self.text(phase, x, 200, self.small)

        self.text("NEXT", x, 250, self.small)
        pygame.draw.rect(self.canvas, (25, 25, 36), (x, 280, 240, 170))
        self.draw_mini_piece(self.next_kind, x, 280)

        self.text("HOLD  [C / SHIFT]", x, 485, self.small)
        pygame.draw.rect(self.canvas, (25, 25, 36), (x, 515, 240, 170))
        if self.hold_kind:
            self.draw_mini_piece(self.hold_kind, x, 515)

        self.text("SPACE     pause", x, 730, self.small)
        self.text("M        music", x, 762, self.small)
        self.text("Arrows/A-D move", x, 794, self.small)
        self.text("UP       hard drop", x, 826, self.small)
        self.text("C/Shift  hold", x, 858, self.small)
        self.text("Cmd/Alt+Enter fullscreen", x, 890, self.small)

    def draw_pause(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA); overlay.fill((0,0,0,205)); self.canvas.blit(overlay,(0,0))
        title=self.big.render("PAUSED",True,COLORS["text"]); self.canvas.blit(title,title.get_rect(center=(WINDOW_W//2,WINDOW_H//2-150)))
        for i,item in enumerate(self.pause_menu_items):
            y=WINDOW_H//2-45+i*75
            if i==self.pause_menu_index: pygame.draw.rect(self.canvas,(82,42,105),(WINDOW_W//2-190,y-10,380,55))
            t=self.font.render(("▶  " if i==self.pause_menu_index else "   ")+item,True,COLORS["text"]); self.canvas.blit(t,t.get_rect(center=(WINDOW_W//2,y+15)))
        hint=self.small.render("↑ ↓ select   ENTER confirm   SPACE continue   ESC menu",True,COLORS["text"]); self.canvas.blit(hint,hint.get_rect(center=(WINDOW_W//2,WINDOW_H//2+210)))

    def choose_story_winner(self):
        """Resolve the 200-line meta choice without changing tetromino geometry."""
        if self.winner_choice == 0:
            self.story_winner = "guardians"
            self.guardians_route = True
            self.phobos_route = False
            self.session_has_victory = True
            self.consecutive_game_overs = 0
            self.horror_piece_mode = False
            self.guardians_gone_this_run = False
            # Guardians victory also returns the entire stack to classic sprite-free Tetris blocks.
            for row in self.board:
                for cell in row:
                    if cell is not None:
                        cell["surface"] = None; cell["plain"] = True
            if self.voice_channel: self.voice_channel.stop()
            self.story200_stage = "guardians_win"
            ending = ASSET_DIR / "audio" / "collection" / "witch_ending.mp3"
            if ending.exists() and pygame.mixer.get_init():
                try: pygame.mixer.music.stop(); pygame.mixer.music.load(str(ending)); pygame.mixer.music.play(-1); pygame.mixer.music.set_volume(.78)
                except pygame.error: pass
        else:
            self.story_winner = "phobos"
            self.guardians_route = False
            self.phobos_route = True
            self.session_has_victory = False
            # 80% horror set, 20% ordinary. If a future horror sprite pack is absent,
            # rendering safely falls back to the ordinary exact tetromino art.
            self.horror_piece_mode = random.random() < 0.80
            self.guardians_gone_this_run = not self.horror_piece_mode
            # The 20% vanilla branch first shows the Guardians being split out
            # of the character art; then gameplay continues with sprite-free blocks.
            if not self.horror_piece_mode:
                # "ordinary pieces" means NO character sprites anywhere on the board,
                # including cells that were already locked before line 200.
                for row in self.board:
                    for cell in row:
                        if cell is not None:
                            cell["surface"] = None
                            cell["plain"] = True
            self.story200_stage = "phobos_win" if self.horror_piece_mode else "phobos_split"
            laugh = self.voice_paths.get("brilliant_laugh")
            if laugh and laugh.exists(): self.play_external_voice(laugh, force=True)
        self.story200_tick = 0

    def continue_after_story200(self):
        self.story_overlay = None
        self.music.set_phase(3 if self.phobos_route else 2, force=True)
        self.music.resume()

    def draw_story200(self):
        # The route takes over the palette immediately after the choice.
        self.draw_background(1 if self.phobos_route and self.story200_stage != "choice" else 2)
        shade=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); shade.fill((0,0,0,165)); self.canvas.blit(shade,(0,0))
        self.ensure_story100_assets()
        if self.story200_stage == "cinematic_reverse":
            title=self.small.render("200 LINES — THE SPELL BREAKS",True,(225,175,255)); self.canvas.blit(title,title.get_rect(center=(WINDOW_W//2,80)))
            active=self.active_intro_characters(); progress=min(1.0,self.story200_tick/max(1,FPS*3.2))
            positions={"will":(110,470),"irma":(225,470),"cornelia":(335,470),"taranee":(455,470),"haylin":(575,470),"caleb":(700,470),"blunk":(810,520)}
            # Reverse transformation: tetromino -> t2 -> t1 -> normal. Removed characters never appear.
            rev_stage=3 if progress<0.25 else 2 if progress<0.52 else 1 if progress<0.78 else 0
            for ch in active:
                key = ch+"_normal" if rev_stage==0 else ch+"_t1" if rev_stage==1 else ch+"_t2" if rev_stage==2 else ch+"_final"
                self.draw_intro_character(key,positions[ch],255 if ch!="blunk" else 215,2)
            self.draw_wrapped_center("ЗАКЛИНАНИЕ РАЗРУШАЕТСЯ...",790,700,self.font,(240,220,255))
            return
        if self.story200_stage == "cinematic_heart":
            active=self.active_intro_characters()
            if self.character_exists("will") and self.story100_assets.get("will_heart"):
                self.draw_story100_sprite(self.story100_assets["will_heart"],(WINDOW_W//2,430),720,2)
                self.draw_wrapped_center("СТРАЖНИЦЫ... МЫ ЕДИНЫ!",830,760,self.font,(250,220,255))
            elif active:
                ch=active[0]; action=self.story100_assets.get(ch+"_action")
                if action: self.draw_story100_sprite(action,(WINDOW_W//2,430),700,2)
                else: self.draw_intro_character(ch+"_normal",(WINDOW_W//2,430),700,2)
                self.draw_wrapped_center("МЫ СНОВА СВОБОДНЫ!",830,760,self.font,(250,220,255))
            else:
                self.draw_wrapped_center("СВЯЗИ ЗАКЛИНАНИЯ ОБОРВАНЫ.",500,760,self.font,(250,220,255))
            return
        if self.story200_stage == "cinematic_phobos":
            # The old 14-frame export had destructively transparent black
            # costume pixels. Use the fully reconstructed RGB pose and animate
            # it with a restrained pulse/jitter instead of showing holes.
            source = self.story100_assets.get("phobos_action") or self.phobos_resistance_body
            if source:
                pulse = int(742 + 18 * math.sin(self.story200_tick / 7.0))
                self.draw_story100_sprite(source,(WINDOW_W//2,430),pulse,3)
            self.draw_wrapped_center("НЕТ... ВЫ НЕ МОЖЕТЕ ОСВОБОДИТЬСЯ!",840,780,self.font,(255,185,210))
            if self.story200_tick%17<5:
                flash=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); flash.fill((210,150,255,75)); self.canvas.blit(flash,(0,0))
            return
        if self.story200_stage == "cinematic_break":
            frames=getattr(self,"story200_collapse_frames",[])
            if frames:
                idx=min(len(frames)-1,int(self.story200_tick/max(1,FPS*3.0)*len(frames)))
                self.draw_story100_sprite(frames[idx],(WINDOW_W//2,430),720,4)
            else:
                src=self.phobos_resistance_body
                if src: self.draw_story100_sprite(src,(WINDOW_W//2,430),760,4)
            # Particle-like dissolve over the supplied collapse animation.
            rng=random.Random(self.story200_tick//2+200)
            for _ in range(80):
                x=rng.randrange(180,720); y=rng.randrange(120,760); r=rng.randrange(1,5)
                pygame.draw.rect(self.canvas,(170,85,210),(x,y,r,r))
            self.draw_wrapped_center("КТО ОКОНЧАТЕЛЬНО ВОЗЬМЁТ КОНТРОЛЬ?",850,800,self.font,(245,225,255))
            return
        if self.story200_stage == "choice":
            t=self.big.render("КТО ПОБЕДИТ?",True,COLORS["accent"]); self.canvas.blit(t,t.get_rect(center=(WINDOW_W//2,250)))
            opts=["СТРАЖНИЦЫ","ФОБОС"]
            box_w, box_h, gap = 310, 100, 36
            start_x = (WINDOW_W - (box_w*2 + gap)) // 2
            for i,label in enumerate(opts):
                r=pygame.Rect(start_x+i*(box_w+gap),420,box_w,box_h)
                if i==self.winner_choice: pygame.draw.rect(self.canvas,(82,42,105),r)
                pygame.draw.rect(self.canvas,COLORS["text"],r,2)
                tx=self.font.render(label,True,COLORS["text"]); self.canvas.blit(tx,tx.get_rect(center=r.center))
            h=self.small.render("← → / MOUSE выбрать   SPACE / CLICK подтвердить   можно вводить секретный код",True,COLORS["text"]); self.canvas.blit(h,h.get_rect(center=(WINDOW_W//2,650)))
            return
        if self.story200_stage == "jetix_thanks":
            self.canvas.fill((5,5,8))
            if self.jetix_logo:
                iw,ih=self.jetix_logo.get_size(); h=360; w=max(1,int(iw*h/ih))
                logo=pygame.transform.scale(self.jetix_logo,(w,h)); self.canvas.blit(logo,logo.get_rect(center=(WINDOW_W//2,390)))
            t=self.big.render("СПАСИБО, JETIX",True,(245,245,245)); self.canvas.blit(t,t.get_rect(center=(WINDOW_W//2,690)))
            sub=self.font.render("ЗА ТО, С ЧЕГО ВСЁ НАЧАЛОСЬ",True,COLORS["accent"]); self.canvas.blit(sub,sub.get_rect(center=(WINDOW_W//2,760)))
            h=self.small.render("SPACE — НАЗАД К ВЫБОРУ",True,COLORS["text"]); self.canvas.blit(h,h.get_rect(center=(WINDOW_W//2,900)))
            return
        if self.story200_stage == "porn_confirm":
            self.canvas.fill((8,8,10))
            t=self.big.render("OPEN RANDOM ADULT SITE?",True,(245,245,245)); self.canvas.blit(t,t.get_rect(center=(WINDOW_W//2,420)))
            sub=self.font.render("Y — OPEN     N / ESC — BACK",True,COLORS["accent"]); self.canvas.blit(sub,sub.get_rect(center=(WINDOW_W//2,535)))
            warn=self.small.render("Откроется один случайный адрес из твоего списка во внешнем браузере.",True,(190,190,200)); self.canvas.blit(warn,warn.get_rect(center=(WINDOW_W//2,610)))
            return
        if self.story200_stage == "phobos_split":
            title=self.font.render("ФОБОС РАЗРУШАЕТ ОБЛИК СТРАЖНИЦ",True,COLORS["danger"]); self.canvas.blit(title,title.get_rect(center=(WINDOW_W//2,120)))
            chars=[ch+"_normal" for ch in ("will","irma","taranee","cornelia","haylin") if self.character_exists(ch)]
            xs=[int(120+i*(620/max(1,len(chars)-1))) if len(chars)>1 else WINDOW_W//2 for i in range(len(chars))]
            progress=min(1.0,self.story200_tick/max(1,FPS*3))
            for key,cx in zip(chars,xs):
                img=self.intro_images.get(key)
                if not img: continue
                target_h=250
                target_w=max(1,int(img.get_width()*target_h/img.get_height()))
                shown=pygame.transform.scale(img,(target_w,target_h))
                shown.set_alpha(max(0,int(255*(1-progress*0.78))))
                half=max(1,target_w//2)
                y=320 + int(18*math.sin(progress*math.pi))
                offset=int(70*progress + 15*math.sin(progress*math.pi*5))
                left=shown.subsurface(pygame.Rect(0,0,half,target_h))
                right=shown.subsurface(pygame.Rect(half,0,target_w-half,target_h))
                self.canvas.blit(left,(cx-target_w//2-offset,y))
                self.canvas.blit(right,(cx-target_w//2+half+offset,y))
                pygame.draw.line(self.canvas,(235,210,255),(cx,y),(cx,y+target_h),max(1,int(5*(1-progress))))
            sub=self.small.render("Персонажи исчезают. Остаётся только геометрия тетромино.",True,COLORS["text"]); self.canvas.blit(sub,sub.get_rect(center=(WINDOW_W//2,690)))
            return
        if self.story200_stage == "guardians_win":
            title=self.big.render("СТРАЖНИЦЫ ПОБЕДИЛИ",True,COLORS["accent"]); self.canvas.blit(title,title.get_rect(center=(WINDOW_W//2,330)))
            sub=self.font.render("Фобос больше не говорит. Свободная игра открыта.",True,COLORS["text"]); self.canvas.blit(sub,sub.get_rect(center=(WINDOW_W//2,430)))
        else:
            title=self.big.render("ФОБОС ПОБЕДИЛ",True,COLORS["danger"]); self.canvas.blit(title,title.get_rect(center=(WINDOW_W//2,330)))
            mode="ЖУТКИЕ ФИГУРЫ — 80%" if self.horror_piece_mode else "ОБЫЧНЫЕ ФИГУРЫ — 20%"
            sub=self.font.render(mode,True,COLORS["text"]); self.canvas.blit(sub,sub.get_rect(center=(WINDOW_W//2,430)))
        h=self.small.render("SPACE — ПРОДОЛЖИТЬ",True,COLORS["text"]); self.canvas.blit(h,h.get_rect(center=(WINDOW_W//2,620)))

    def draw_wrapped_center(self, text, y, max_width=720, font=None, color=(240,225,245)):
        font=font or self.font
        words=str(text).split(); lines=[]; cur=""
        for word in words:
            test=(cur+" "+word).strip()
            if font.size(test)[0] <= max_width: cur=test
            else:
                if cur: lines.append(cur)
                cur=word
        if cur: lines.append(cur)
        for i,line in enumerate(lines[:5]):
            surf=font.render(line,True,color); self.canvas.blit(surf,surf.get_rect(center=(WINDOW_W//2,y+i*(font.get_height()+8))))

    def draw_phobos_window_parallax(self):
        """Move the separate Meridian layer a few pixels behind both windows."""
        outside = self.phobos_room_outside
        if outside is None:
            return
        tick = self.phobos_room_tick
        drift_x = int(round(math.sin(tick / 210.0) * 6.0))
        drift_y = int(round(math.sin(tick / 285.0) * 2.0))
        # Pane rectangles follow background_v2 at the fixed 860x1060 canvas.
        # Drawing only into the glass keeps the existing mullions and curtains
        # intact while the exterior remains an independent portable layer.
        windows = (
            ((123, 155), 104, ((0, 0, 62, 111), (71, 0, 61, 111),
                               (0, 122, 62, 225), (71, 122, 61, 225))),
            ((590, 155), 270, ((0, 0, 72, 111), (82, 0, 71, 111),
                               (0, 122, 72, 225), (82, 122, 71, 225))),
        )
        for (window_x, window_y), source_x, panes in windows:
            for local_x, local_y, width, height in panes:
                destination = (window_x + local_x, window_y + local_y)
                source = pygame.Rect(
                    source_x + local_x + drift_x,
                    10 + local_y + drift_y,
                    width,
                    height,
                )
                self.canvas.blit(outside, destination, source)

    def draw_phobos_room(self):
        if self.phobos_room_stage == "crash":
            self.draw_background(1)
            shade=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); shade.fill((0,0,0,110)); self.canvas.blit(shade,(0,0))
            snap=self.canvas.copy()
            for y in range(0,WINDOW_H,42):
                off=random.randint(-45,45); self.canvas.blit(snap,(off,y),pygame.Rect(0,y,WINDOW_W,30))
            err=self.big.render("FATAL ERROR",True,(245,70,90)); self.canvas.blit(err,err.get_rect(center=(WINDOW_W//2,430)))
            sub=self.small.render("PHOBOS.EXE HAS TAKEN CONTROL",True,COLORS["text"]); self.canvas.blit(sub,sub.get_rect(center=(WINDOW_W//2,500)))
            return
        if self.phobos_room_stage == "blackout": self.canvas.fill((0,0,0)); return
        room_source=None
        if self.phobos_room_bg_frames:
            # Slow smoke/city cycling; lightning frame is deliberately rare.
            sec=self.phobos_room_tick/max(1,FPS)
            if int(sec)%47==0 and (self.phobos_room_tick%FPS)<10 and len(self.phobos_room_bg_frames)>2: bi=2
            else: bi=(int(sec//8)%2) if len(self.phobos_room_bg_frames)>1 else 0
            room_source=self.phobos_room_bg_frames[bi]
        elif self.phobos_room_bg:
            room_source=self.phobos_room_bg
        if room_source:
            iw,ih=room_source.get_size(); scale=max(WINDOW_W/iw,WINDOW_H/ih)
            scaled=pygame.transform.smoothscale(room_source,(max(1,int(iw*scale)),max(1,int(ih*scale))))
            crop=pygame.Rect((scaled.get_width()-WINDOW_W)//2,(scaled.get_height()-WINDOW_H)//2,WINDOW_W,WINDOW_H)
            room_render=scaled.subsurface(crop).copy(); self.canvas.blit(room_render,(0,0))
            self.draw_phobos_window_parallax()
        else:
            room_render=None; self.canvas.fill((12,4,8))
        shade=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); shade.fill((0,0,0,35)); self.canvas.blit(shade,(0,0))
        if self.phobos_room_emotions:
            src=self.phobos_room_emotions[self.phobos_room_emotion % len(self.phobos_room_emotions)]
            h=565; w=max(1,int(src.get_width()*h/src.get_height())); img=pygame.transform.smoothscale(src,(w,h))
            self.canvas.blit(img,img.get_rect(midbottom=(WINDOW_W//2,900)))
        if room_render:
            # The table is baked into background_v2. Repaint it from its top
            # edge over Phobos so every pose sits convincingly behind it.
            table_top=700
            self.canvas.blit(room_render,(0,table_top),pygame.Rect(0,table_top,WINDOW_W,WINDOW_H-table_top))
        text=self.current_phobos_room_text()
        if text:
            box=pygame.Surface((WINDOW_W-70,180),pygame.SRCALPHA); box.fill((5,2,9,220)); pygame.draw.rect(box,(105,45,125,255),box.get_rect(),3)
            self.canvas.blit(box,(35,850))
            name=self.small.render("ФОБОС",True,(220,120,245)); self.canvas.blit(name,(65,870))
            self.draw_wrapped_center(text,910,WINDOW_W-150,self.small,(245,235,250))

    def draw_story_overlay(self):
        if self.story_overlay == 100:
            self.draw_story100()
            return
        if self.story_overlay == 200:
            self.draw_story200()
            return
        if self.story_overlay == 300:
            self.draw_phobos_room()
            return
        self.draw_background(2)
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.canvas.blit(overlay, (0, 0))
        title = self.big.render("YOU WIN", True, COLORS["accent"])
        self.canvas.blit(title, title.get_rect(center=(WINDOW_W//2, WINDOW_H//2-105)))
        m = self.font.render("PHOBOS DEFEATED", True, COLORS["text"])
        self.canvas.blit(m, m.get_rect(center=(WINDOW_W//2, WINDOW_H//2-25)))
        m2 = self.font.render("FREE PLAY UNLOCKED", True, COLORS["text"])
        self.canvas.blit(m2, m2.get_rect(center=(WINDOW_W//2, WINDOW_H//2+25)))
        c = self.small.render("SPACE — CONTINUE", True, COLORS["text"])
        self.canvas.blit(c, c.get_rect(center=(WINDOW_W//2, WINDOW_H//2+105)))

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.canvas.blit(overlay, (0, 0))
        over_title = "ИГРА ЗАКОНЧЕНА" if self.empty_roster_bored else ("FREE PLAY — RUN OVER" if self.lines >= LINES_PHASE2 or self.session_has_victory else "GAME OVER")
        t = self.big.render(over_title, True, COLORS["danger"] if over_title == "GAME OVER" else COLORS["accent"])
        self.canvas.blit(t, t.get_rect(center=(WINDOW_W//2, WINDOW_H//2-120)))
        if self.empty_roster_bored:
            m = self.font.render("ФОБОС ЗАСКУЧАЛ", True, COLORS["text"])
        else:
            m = self.font.render(f"LINES {self.lines}     SCORE {self.score}", True, COLORS["text"])
        self.canvas.blit(m, m.get_rect(center=(WINDOW_W//2, WINDOW_H//2-55)))
        for i, item in enumerate(self.game_over_items):
            rect = self.game_over_rects()[i]
            if i == self.game_over_index:
                pygame.draw.rect(self.canvas, (82, 42, 105), rect)
            label = self.font.render(("▶  " if i == self.game_over_index else "   ") + item, True, COLORS["text"])
            self.canvas.blit(label, label.get_rect(center=rect.center))
        c = self.small.render("↑ ↓ / mouse   ENTER / click     ESC — MENU", True, COLORS["text"])
        self.canvas.blit(c, c.get_rect(center=(WINDOW_W//2, WINDOW_H//2+230)))

    def draw_secret_effects(self):
        if not self.secret_gameplay_context():
            return
        if self.matrix_timer > 0 or self.vtd_active:
            green = (40, 255, 90)
            # MATRIX is interface-only; VTD additionally recolors the whole gameplay render.
            pygame.draw.rect(self.canvas, green, (BOARD_X, BOARD_Y, BOARD_W*CELL, BOARD_H*CELL), 3)
            for y in range(BOARD_H + 1):
                pygame.draw.line(self.canvas, (25, 100, 45), (BOARD_X, BOARD_Y+y*CELL), (BOARD_X+BOARD_W*CELL, BOARD_Y+y*CELL), 1)
            hud_x = BOARD_X + BOARD_W*CELL + 20
            pygame.draw.rect(self.canvas, green, (hud_x, 20, HUD_W-20, WINDOW_H-40), 2)
            for i in range(18):
                ch = random.choice("01<>[]{}WITCH")
                surf = self.small.render(ch, True, green)
                self.canvas.blit(surf, (hud_x + random.randrange(10, HUD_W-50), random.randrange(20, WINDOW_H-40)))
            if self.vtd_active and self.vtd_intro_timer > 0:
                a = int(150 * (self.vtd_intro_timer / max(1, int(FPS * 0.35))))
                flash = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
                flash.fill((20, 255, 75, a))
                self.canvas.blit(flash, (0, 0))

        if self.jetix_timer > 0:
            # Jetix v6.5: corner cameo, bounce -> wink/squash -> somersault -> exit.
            # Colored confetti only; tetromino art and physics remain untouched.
            palette = [(255,70,70),(255,190,40),(80,220,120),(80,180,255),(210,90,255),(255,110,190)]
            elapsed = FPS * 6 - self.jetix_timer
            for i in range(34):
                x = (i * 89 + elapsed * (4 + i % 3)) % WINDOW_W
                y = (i * 137 + elapsed * (3 + i % 4)) % WINDOW_H
                col = palette[i % len(palette)]
                if i % 3 == 0:
                    pygame.draw.rect(self.canvas, col, (x, y, 6, 10))
                else:
                    pygame.draw.circle(self.canvas, col, (x, y), 3 + i % 4)
            if self.jetix_logo:
                total = FPS * 6
                t = elapsed / total
                base_w = 190
                base_h = int(self.jetix_logo.get_height() * (base_w / self.jetix_logo.get_width()))
                # Enter/bounce during first third, then spin, then fly upward/right.
                if t < .28:
                    local = t / .28
                    yoff = int(-55 * abs(__import__('math').sin(local * __import__('math').pi * 2.2)) * (1-local*.5))
                    angle = 0
                elif t < .72:
                    local = (t-.28)/.44
                    yoff = int(-10 * __import__('math').sin(local * __import__('math').pi*2))
                    angle = int(360 * local)
                else:
                    local = (t-.72)/.28
                    yoff = int(-260 * local)
                    angle = int(360 + 220 * local)
                # A quick horizontal squash is the playful "wink" beat.
                wink = .82 if .18 < t < .23 else 1.0
                logo = pygame.transform.scale(self.jetix_logo, (max(1,int(base_w*wink)), base_h))
                logo = pygame.transform.rotate(logo, angle)
                x = WINDOW_W - 145 + int(110 * max(0, (t-.72)/.28))
                y = 120 + yoff
                self.canvas.blit(logo, logo.get_rect(center=(x, y)))

        if self.secret_overlay == "ru_18":
            overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 80))
            self.canvas.blit(overlay, (0, 0))
            t = pygame.font.SysFont("Arial", 190, bold=True).render("18+", True, (255, 255, 255))
            self.canvas.blit(t, t.get_rect(center=(WINDOW_W//2, WINDOW_H//2)))

        if self.secret_overlay == "porn_gallery":
            overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 235))
            self.canvas.blit(overlay, (0, 0))
            if self.secret_image:
                iw, ih = self.secret_image.get_size()
                scale = min((WINDOW_W-100)/iw, (WINDOW_H-150)/ih)
                shown = pygame.transform.scale(self.secret_image, (max(1,int(iw*scale)), max(1,int(ih*scale))))
                self.canvas.blit(shown, shown.get_rect(center=(WINDOW_W//2, WINDOW_H//2-25)))
            c = self.small.render("SPACE — CONTINUE", True, COLORS["text"])
            self.canvas.blit(c, c.get_rect(center=(WINDOW_W//2, WINDOW_H-45)))

    def blit_cover(self, image, rect):
        if image is None:
            return
        iw, ih = image.get_size()
        rw, rh = rect.width, rect.height
        scale = max(rw / iw, rh / ih)
        shown = pygame.transform.scale(image, (max(1, int(iw*scale)), max(1, int(ih*scale))))
        crop = pygame.Rect((shown.get_width()-rw)//2, (shown.get_height()-rh)//2, rw, rh)
        self.canvas.blit(shown, rect.topleft, crop)

    def draw_background(self, key):
        self.canvas.fill(COLORS["bg"])
        img = self.backgrounds.get(key)
        if img:
            self.blit_cover(img, pygame.Rect(0, 0, WINDOW_W, WINDOW_H))
            veil = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            veil.fill((5, 6, 14, 72))
            self.canvas.blit(veil, (0, 0))

    def current_menu_face(self):
        # Small SNES idle animation: neutral -> half blink -> blink -> neutral.
        cyc = self.menu_tick % 240
        if 190 <= cyc < 194:
            return "half_blink"
        if 194 <= cyc < 199:
            return "blink"
        if 199 <= cyc < 203:
            return "half_blink"
        # Selection-based expressions make the menu feel reactive already.
        if self.mode == "menu" and self.menu_index == 2:
            return "suspicious"
        if self.mode == "menu" and self.menu_index == 3:
            return "smirk"
        return "neutral"

    def ensure_story100_assets(self):
        if self.story100_loaded:
            return
        mapping = {
            "heart_mask": "heart_kandrakar_mask.png",
            "jetix_mask": "jetix_mask.png",
            "will_action": "will_action.png",
            "will_heart": "will_heart.png",
            "phobos_action": "phobos_action.png",
            "taranee_action": "taranee_action.png",
            "cornelia_action": "cornelia_action.png",
            "haylin_action": "haylin_action.png",
            "caleb_action": "caleb_action.png",
        }
        for key, name in mapping.items():
            fp = LINES100_DIR / name
            if fp.exists():
                try:
                    if key.endswith("_mask"):
                        self.story100_assets[key] = pygame.image.load(str(fp)).convert_alpha()
                    else:
                        self.story100_assets[key] = load_clean_alpha(fp)
                except pygame.error:
                    pass
        # v6.22 third-cutscene source sheets supplied earlier by the user.
        self.story200_assets = getattr(self,"story200_assets",{})
        for key,name in {"phobos_collapse":"phobos_collapse_sheet.png","will_heart_sheet":"will_heart_sheet.png","phobos_action_sheet":"phobos_action_sheet.png"}.items():
            fp=ASSET_DIR / "cutscenes" / "lines200" / name
            if fp.exists():
                try: self.story200_assets[key]=pygame.image.load(str(fp)).convert_alpha()
                except pygame.error: pass
        self.story200_action_frames=[]
        action_frames_dir=ASSET_DIR / "cutscenes" / "lines200" / "phobos_action_frames"
        for fp in sorted(action_frames_dir.glob("frame_*.png")):
            try: self.story200_action_frames.append(load_clean_alpha(fp))
            except pygame.error: pass
        if not self.story200_action_frames and self.story200_assets.get("phobos_action_sheet"):
            sheet=self.story200_assets["phobos_action_sheet"]
            for x,y,w,h in PHOBOS_ACTION_RECTS:
                rect=pygame.Rect(x,y,w,h).clip(sheet.get_rect())
                if rect.width and rect.height:
                    self.story200_action_frames.append(clean_alpha_surface(sheet.subsurface(rect).copy(), 24))
        self.story200_collapse_frames=[]
        for fp in sorted((ASSET_DIR / "cutscenes" / "lines200" / "phobos_collapse_frames").glob("frame_*.png")):
            try: self.story200_collapse_frames.append(pygame.image.load(str(fp)).convert_alpha())
            except pygame.error: pass
        self.story100_loaded = True

    def start_story100(self):
        self.ensure_story100_assets()
        self.story_overlay = 100
        self.story100_stage = "glitch"
        self.story100_tick = 0
        self.story100_seed = random.randrange(1_000_000)
        r = random.random()
        # Exact requested distribution: 50% plain terminal; the other 50%
        # split equally into four 12.5% text-silhouette easter eggs.
        if r < 0.50:
            self.story100_variant = "plain"
        elif r < 0.625:
            self.story100_variant = "kandrakar"
        elif r < 0.750:
            self.story100_variant = "jetix"
        elif r < 0.875:
            self.story100_variant = "heart"
        else:
            self.story100_variant = "q"
        jokes = [
            "> guardian_shape.dll stopped responding",
            "> expected: GUARDIAN   received: TETROMINO",
            "> prophecy.txt has been modified",
            "> administrator privileges revoked: PHOBOS",
            "> fourth_wall.dll ... FILE NOT FOUND",
            "> pygame window detected. please pretend you did not see this",
            "> checking SPACE key ... suspicious",
            "> searching for competent servants ... 0 results",
            "> PHOBOS confidence: 100% -> recalculating -> 17%",
            "> spell warranty expired 1847 years ago",
            "> technical support has been imprisoned",
            "> ERROR CODE: W.I.T.C.H.",
            "> this is probably fine. correction: not fine.",
            "> someone is reading these logs",
            "> stop reading the logs. these are private.",
            "> save file located. deleting... PERMISSION DENIED. lucky you.",
            "> have you tried turning the Veil off and on again?",
            "> current runtime: pygame ... wait, what is pygame?",
            "> PLAYER detected. there should not be a player.",
            "> touch grass protocol unavailable in Meridian",
            "> checking Blunk ... honestly, no idea.",
        ]
        rng = random.Random(self.story100_seed)
        blocked=[]
        for ch,label in {"will":"will","irma":"irma","taranee":"taranee","cornelia":"cornelia","haylin":"hay","caleb":"caleb","blunk":"blunk"}.items():
            if not self.character_exists(ch): blocked.append(label)
        filtered=[j for j in jokes if not any(b.lower() in j.lower() for b in blocked)]
        self.story100_jokes = rng.sample(filtered, k=min(4,len(filtered)))
        speaker_lines = {
            "will": "Заклинание слабеет!",
            "irma": "Наконец-то! Я снова чувствую себя собой!",
            "cornelia": "Он теряет над нами контроль.",
            "taranee": "Его магия становится нестабильной.",
            "haylin": "Я снова чувствую свою силу!",
            "caleb": "Фобос теряет контроль.",
            "blunk": "Бланк знал, что так и будет!",
        }
        speaker_pool=[ch for ch in speaker_lines if self.character_exists(ch)]
        if rng.random() < 0.70 and "will" in speaker_pool and len(speaker_pool)>1:
            speaker_pool.remove("will")
        self.story100_speaker = rng.choice(speaker_pool) if speaker_pool else None
        if self.story100_speaker:
            self.story100_speaker_line = "Мы всё ещё здесь!" if len(self.active_intro_characters()) == 1 else speaker_lines[self.story100_speaker]
        else:
            self.story100_speaker_line = ""
        self.story100_sfx_played.clear()
        self.story100_silhouette_cache.clear()

    def finish_story100(self):
        self.story_overlay = None
        self.story100_stage = "done"
        self.story100_tick = 0
        if self.collection_cutscene:
            self.collection_cutscene=False; self.mode="collection"; self.collection_page="CUTSCENES"; self.collection_item_index=0
            self.music.set_phase(-1,force=True)
        elif not self.vtd_active:
            self.music.set_phase(1, force=True)

    def story100_sfx(self, tag, filename, volume=0.8):
        if tag in self.story100_sfx_played or not self.story100_channel:
            return
        fp = SFX_DIR / filename
        if not fp.exists():
            return
        try:
            snd = pygame.mixer.Sound(str(fp)); snd.set_volume(volume)
            self.story100_channel.play(snd)
            self.story100_sfx_played.add(tag)
        except pygame.error:
            pass

    def update_story100(self):
        self.story100_tick += 1
        t = self.story100_tick
        stage = self.story100_stage
        if stage == "glitch":
            # Fake audio-driver failure: the current gameplay track stutters in
            # volume, then vanishes before the black terminal boot.
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy() and t < 56:
                pygame.mixer.music.set_volume(0.18 if (t // 5) % 3 == 1 else 0.72)
            if t == 56:
                self.music.pause()
            if t > 78:
                self.story100_stage, self.story100_tick = "blackout", 0
                self.story100_sfx_played.clear()
        elif stage == "blackout" and t > 42:
            self.story100_stage, self.story100_tick = "terminal", 0
        elif stage == "terminal" and t > 320:
            self.story100_stage, self.story100_tick = "wait_key", 0
        elif stage == "after_key" and t > 48:
            self.story100_stage, self.story100_tick = "hall", 0
            self.story100_sfx_played.clear()
        elif stage == "hall" and t > 115:
            self.story100_stage, self.story100_tick = "guardian", 0
        elif stage == "guardian" and t > 190:
            self.story100_stage, self.story100_tick = "phobos", 0
            self.story100_sfx_played.clear()
        elif stage == "phobos" and t > 220:
            self.story100_stage, self.story100_tick = "title", 0
            self.story100_sfx_played.clear()

    def sprite_sheet_frame(self, surf, cols, rows, index):
        """Return one cell from a sprite sheet. Never display the whole action sheet."""
        if surf is None: return None
        w,h=surf.get_size()
        if w < 600 or h < 600: return surf
        cw=max(1,w//cols); ch=max(1,h//rows)
        index=max(0,min(cols*rows-1,int(index)))
        r=index//cols; c=index%cols
        frame=pygame.Surface((cw,ch),pygame.SRCALPHA)
        frame.blit(surf,(0,0),pygame.Rect(c*cw,r*ch,cw,ch))
        # crop transparent borders
        br=frame.get_bounding_rect(min_alpha=8)
        return frame.subsurface(br).copy() if br.width and br.height else frame

    def draw_story100_sprite(self, surf, center, max_h=650, jitter=0):
        if not surf:
            return
        iw, ih = surf.get_size()
        scale = min(max_h/max(1,ih), 760/max(1,iw))
        shown = pygame.transform.scale(surf, (max(1,int(iw*scale)), max(1,int(ih*scale))))
        dx = random.randint(-jitter,jitter) if jitter else 0
        dy = random.randint(-jitter,jitter) if jitter else 0
        self.canvas.blit(shown, shown.get_rect(center=(center[0]+dx, center[1]+dy)))

    def story100_mask_surface(self, variant, size=(420, 500)):
        key = (variant, size)
        if key in self.story100_masks:
            return self.story100_masks[key]
        w,h=size
        mask = pygame.Surface((w,h), pygame.SRCALPHA)
        if variant in ("kandrakar", "jetix"):
            src = self.story100_assets.get("heart_mask" if variant == "kandrakar" else "jetix_mask")
            if src:
                sw,sh=src.get_size(); scale=min(w/sw,h/sh)
                scaled=pygame.transform.scale(src,(max(1,int(sw*scale)),max(1,int(sh*scale))))
                mask.blit(scaled, scaled.get_rect(center=(w//2,h//2)))
                self.story100_masks[key] = mask
                return mask
        if variant == "heart":
            # mathematical heart silhouette
            for yy in range(h):
                y = (yy-h*0.45)/(h*0.42)
                for xx in range(0,w,2):
                    x = (xx-w/2)/(w*0.43)
                    v=(x*x+y*y-1)**3-x*x*y*y*y
                    if v <= 0:
                        pygame.draw.rect(mask,(255,255,255,255),(xx,yy,2,2))
            self.story100_masks[key] = mask
            return mask
        # Large Q: thick ring plus tail.
        pygame.draw.ellipse(mask,(255,255,255,255),(45,35,w-90,h-130),28)
        pygame.draw.line(mask,(255,255,255,255),(int(w*0.58),int(h*0.68)),(int(w*0.86),int(h*0.96)),32)
        self.story100_masks[key] = mask
        return mask

    def draw_story100_text_silhouette(self, variant, rect):
        cache_key = (variant, rect.size, self.story100_seed)
        cached = self.story100_silhouette_cache.get(cache_key)
        if cached is not None:
            self.canvas.blit(cached, rect.topleft)
            return
        mask = self.story100_mask_surface(variant, rect.size)
        tex = pygame.Surface(rect.size, pygame.SRCALPHA)
        words = ["ERROR","FAILED","UNSTABLE","PHOBOS","MERIDIAN","KANDRAKAR","SPELL","CONTROL","LOST","DENIED","WARNING","49%","PLAYER","Q","JETIX","W.I.T.C.H.","FATAL","RECOVERY"]
        for ch,label in {"will":"WILL","irma":"IRMA","taranee":"TARANEE","cornelia":"CORNELIA","haylin":"HAY_LIN","caleb":"CALEB","blunk":"BLUNK"}.items():
            if self.character_exists(ch): words.append(label)
        rng = random.Random(self.story100_seed + 91)
        y=0
        while y < rect.height:
            line=[]
            while self.story100_small_mono.size(" ".join(line))[0] < rect.width+120:
                line.append(rng.choice(words))
            rendered=self.story100_small_mono.render(" ".join(line),True,(245,70+rng.randrange(0,90),180+rng.randrange(0,70)))
            tex.blit(rendered,(rng.randrange(-80,0),y))
            y += 14
        tex.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        self.story100_silhouette_cache[cache_key] = tex
        self.canvas.blit(tex,rect.topleft)

    def draw_story100_terminal(self):
        self.canvas.fill((0,0,0))
        green=(100,255,120); red=(255,75,90); pink=(255,80,190); amber=(235,190,85)
        t=330 if self.story100_stage == "wait_key" else self.story100_tick
        lines=["MERIDIAN CONTROL SYSTEM","PHOBOS SPELL ENGINE v1.0","","> checking guardian bindings..."]
        diag={"will":"WILL","irma":"IRMA","taranee":"TARANEE","cornelia":"CORNELIA","haylin":"HAY LIN","caleb":"CALEB","blunk":"BLUNK"}
        for ch in self.intro_characters:
            if self.character_exists(ch): lines.append(f"{diag[ch]:<14} UNSTABLE")
        if not self.active_intro_characters(): lines.append("NO GUARDIANS DETECTED")
        lines += ["","> integrity: 49%","> attempting recovery...","RECOVERY FAILED","FATAL ERROR: CONTROL OVER GUARDIANS LOST."]
        # reveal diagnostic lines gradually
        visible=max(1,min(len(lines),t//13))
        y=45
        for i,line in enumerate(lines[:visible]):
            col=red if ("FAILED" in line or "FATAL" in line) else green
            self.canvas.blit(self.story100_mono.render(line,True,col),(45,y)); y+=25
        # four random fourth-wall jokes rotate in the lower-left area
        if t>150:
            jy=500
            for j in self.story100_jokes[:max(1,min(4,(t-150)//34+1))]:
                self.canvas.blit(self.story100_small_mono.render(j,True,amber),(45,jy)); jy+=22
        # 50% no image; each special image exactly 12.5% overall.
        if self.story100_variant != "plain" and t>105:
            self.draw_story100_text_silhouette(self.story100_variant, pygame.Rect(WINDOW_W-455,120,400,500))
            labels={"kandrakar":"HEART OF KANDRAKAR","jetix":"JETIX SIGNAL","heart":"HEART?","q":"UNAUTHORIZED COMMAND: Q"}
            self.canvas.blit(self.story100_mono.render(labels[self.story100_variant],True,pink),(WINDOW_W-450,635))
        if self.story100_stage == "wait_key":
            blink=(self.menu_tick//24)%2==0
            if blink:
                msg=self.story100_mono.render("PRESS ANY KEY",True,green)
                self.canvas.blit(msg,msg.get_rect(center=(WINDOW_W//2,WINDOW_H-45)))

    def draw_story100_dialogue(self, speaker, line):
        box = pygame.Surface((WINDOW_W-90, 170), pygame.SRCALPHA)
        box.fill((0,0,0,210))
        pygame.draw.rect(box,(150,90,190,230),box.get_rect(),3)
        self.canvas.blit(box,(45,WINDOW_H-205))
        self.text(speaker,72,WINDOW_H-185,self.small,COLORS["accent"])
        chars=min(len(line),max(0,self.story100_tick//3))
        shown=line[:chars]
        words, rows, cur = shown.split(), [], ""
        for w in words:
            test=(cur+" "+w).strip()
            if self.font.size(test)[0] > WINDOW_W-155:
                if cur: rows.append(cur)
                cur=w
            else:
                cur=test
        if cur: rows.append(cur)
        for i,row in enumerate(rows[:3]):
            self.text(row,72,WINDOW_H-145+i*36,self.font)

    def draw_story100(self):
        stage,t=self.story100_stage,self.story100_tick
        if stage == "glitch":
            base=self.canvas.copy()
            # Horizontal slice corruption + increasingly frequent blackouts.
            for i in range(14):
                y=random.randrange(0,WINDOW_H-20); hh=random.randrange(4,30); dx=random.randrange(-55,56)
                self.canvas.blit(base,(dx,y),pygame.Rect(0,y,WINDOW_W,hh))
            if (t//7)%3==1:
                flash=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); flash.fill((220,230,255,35)); self.canvas.blit(flash,(0,0))
            if t>56 and t%9<4:
                self.canvas.fill((0,0,0))
            return
        if stage == "blackout":
            self.canvas.fill((0,0,0))
            if t>18:
                cur=self.story100_mono.render("_",True,(100,255,120)); self.canvas.blit(cur,(38,42))
            return
        if stage in ("terminal","wait_key"):
            self.draw_story100_terminal(); return
        if stage == "after_key":
            self.canvas.fill((0,0,0))
            self.story100_sfx("lightning","intro/lightning.wav",0.86)
            msg=self.story100_mono.render("ERROR: PLAYER PRESSED A KEY",True,(255,70,90))
            self.canvas.blit(msg,msg.get_rect(center=(WINDOW_W//2,WINDOW_H//2)))
            if t>24 and t%4<2:
                flash=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); flash.fill((225,205,255,110)); self.canvas.blit(flash,(0,0))
            return
        # Reveal what the fake crash really was: the spell itself destabilising.
        self.canvas.fill((0,0,0))
        self.blit_cover(self.intro_images.get("hall"),pygame.Rect(0,0,WINDOW_W,WINDOW_H))
        veil=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); veil.fill((20,0,35,85)); self.canvas.blit(veil,(0,0))
        if stage == "hall":
            self.draw_intro_hall_group()
            if t%22<6:
                # Character forms flicker between human and tetromino for a few frames.
                for ch,pos in {"will":(110,470),"irma":(225,450),"cornelia":(335,455),"taranee":(545,455),"haylin":(655,450),"caleb":(760,470),"blunk":(820,560)}.items():
                    if self.character_exists(ch): self.draw_intro_character(ch+"_final",pos,245 if ch!="blunk" else 205,2)
            if self.character_exists("will") and 88 <= t <= 104 and self.story100_assets.get("will_heart"):
                flash=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); flash.fill((245,185,255,55)); self.canvas.blit(flash,(0,0))
                self.draw_story100_sprite(self.story100_assets["will_heart"],(WINDOW_W//2,430),670,2)
            return
        if stage == "guardian":
            ch=self.story100_speaker
            if not ch:
                self.draw_story100_dialogue("SYSTEM","НЕКОМУ СОПРОТИВЛЯТЬСЯ.")
                return
            action = self.story100_assets.get(ch + "_action")
            if action:
                self.draw_story100_sprite(action,(WINDOW_W//2,420),700,2)
            else:
                self.draw_intro_character(ch+"_normal",(WINDOW_W//2,430),700 if ch!="blunk" else 580,2)
            self.draw_story100_dialogue(self.intro_names[ch],self.story100_speaker_line)
            return
        if stage == "phobos":
            if t == 106:
                pays=[self.voice_paths.get("pay_short"),self.voice_paths.get("pay_full")]
                pays=[p for p in pays if p and p.exists()]
                if pays: self.play_external_voice(random.choice(pays), force=True)
            if t<105 and self.story100_assets.get("phobos_action"):
                src=self.sprite_sheet_frame(self.story100_assets["phobos_action"], 4, 4, min(15, t//7))
                self.draw_story100_sprite(src,(WINDOW_W//2,420),720,3)
            else:
                self.draw_story100_sprite(self.phobos_resistance_body,(WINDOW_W//2,450),760,2)
            line="Нет... моё заклинание!" if t<105 else "Вы за это заплатите!"
            self.draw_story100_dialogue("ФОБОС",line)
            if t%17<4:
                flash=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); flash.fill((210,170,255,70)); self.canvas.blit(flash,(0,0))
            return
        # title
        self.draw_background(1)
        shade=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); shade.fill((0,0,0,145)); self.canvas.blit(shade,(0,0))
        self.draw_story100_sprite(self.phobos_resistance_body,(WINDOW_W-160,470),690,0)
        a=self.big.render("ЗАКЛИНАНИЕ СЛАБЕЕТ",True,(225,175,255)); self.canvas.blit(a,a.get_rect(center=(WINDOW_W//2-70,WINDOW_H//2-55)))
        b=self.font.render("СОПРОТИВЛЯЙТЕСЬ",True,COLORS["text"]); self.canvas.blit(b,b.get_rect(center=(WINDOW_W//2-70,WINDOW_H//2+25)))
        c=self.small.render("SPACE — CONTINUE",True,COLORS["text"]); self.canvas.blit(c,c.get_rect(center=(WINDOW_W//2-70,WINDOW_H//2+95)))

    def intro_play_music(self, stage):
        if self.intro_music_stage == stage or not pygame.mixer.get_init(): return
        self.intro_music_stage = stage
        folder = MUSIC_ROOT / "intro" / stage
        files = self.music.scan(folder)
        if not files:
            fallback = ASSET_DIR / "audio" / "collection" / "intro_music.mp3"
            files = [fallback] if fallback.exists() else []
        if files:
            chosen = random.choice(files)
            # All current intro stages use the same fallback track. Do not
            # restart it at scene boundaries; a future stage-specific file
            # will still replace it normally.
            if self.intro_music_path == chosen and pygame.mixer.music.get_busy():
                return
            try:
                pygame.mixer.music.stop(); pygame.mixer.music.load(str(chosen)); pygame.mixer.music.play(-1); pygame.mixer.music.set_volume(0.72)
                self.intro_music_path = chosen
            except pygame.error: pass

    def restart_intro(self):
        # Replayable from the main menu; reroll the random speaker/branch every time.
        self.intro_scene = 0
        self.intro_scene_tick = 0
        self.intro_tick = 0
        self.intro_music_stage = None
        self.intro_music_path = None
        self.intro_scene_sfx_played.clear()
        self.intro_text_last_blip_char = -1
        self.intro_voice_played = False
        self.intro_primary_character = "will" if self.character_exists("will") else self.pick_active_character()
        active_nonwill=[ch for ch in self.active_intro_characters() if ch in self.intro_opening_lines]
        self.intro_second_character = random.choice(active_nonwill) if active_nonwill else self.pick_active_character()
        self.intro_second_line = random.choice(self.intro_opening_lines.get(self.intro_second_character,["Мы не сдадимся!"])) if self.intro_second_character else ""
        self.intro_phobos_line = random.choice(("Кончено?! Ха! Всё только начинается!",
                                                "Кончено?! Вы ещё ничего не видели!"))
        active=self.active_intro_characters()
        self.intro_transform_all = bool(active) and (random.random() < 0.50)
        self.intro_transform_character = random.choice(active) if active else None
        self.intro_horror_irma = (random.randrange(10) == 0)
        self.intro_transform_line = random.choice(self.intro_transform_lines[self.intro_transform_character]) if self.intro_transform_character else ""
        candidates = [
            (VOICE_DIR / "extra2" / "your_power_is_nothing.wav", "Теперь ваша сила против моей — ничто.", 20),
            (VOICE_DIR / "extra2" / "new_era_phobos.wav", "Начинается новая эра — эра Фобоса.", 16),
            (VOICE_DIR / "dark_side.mp3", "Ты познаешь всю мощь тёмной стороны.", 16),
            (VOICE_DIR / "extra" / "brilliant_laugh.wav", "Ха-ха-ха!", 14),
            (VOICE_DIR / "extra" / "lets_begin.wav", "Ну что же. Начнём.", 12),
            (VOICE_DIR / "meridian_mine.mp3", "Меридиан принадлежит мне.", 10),
            (VOICE_DIR / "extra2" / "haha_no_way.wav", "Ха! Не выйдет.", 12),
        ]
        candidates = [(p,l,w) for p,l,w in candidates if p.exists()]
        if candidates:
            chosen = random.choices(candidates, weights=[x[2] for x in candidates], k=1)[0]
            self.intro_final_voice_path, self.intro_final_voice_label = chosen[0], chosen[1]
        if self.intro_voice_channel: self.intro_voice_channel.stop()
        if self.intro_text_channel: self.intro_text_channel.stop()
        self.mode = "intro"

    def finish_intro(self):
        if self.intro_voice_channel:
            self.intro_voice_channel.stop()
        if self.collection_cutscene:
            self.collection_cutscene = False
            self.mode = "collection"
            self.collection_page = "CUTSCENES"
            self.collection_item_index = 0
        else:
            self.mode = "menu"
        self.music.special_lock = False
        self.music.set_phase(-1, force=True)

    def advance_intro(self):
        self.intro_scene += 1
        self.intro_scene_tick = 0
        self.intro_voice_played = False
        self.intro_text_last_blip_char = -1
        if self.intro_text_channel: self.intro_text_channel.stop()
        if self.intro_scene >= 8:
            self.finish_intro()

    def draw_intro_character(self, key, center, max_h=650, jitter=0, alpha=255):
        im = self.intro_images.get(key)
        if not im:
            return
        iw, ih = im.get_size()
        scale = min(max_h / max(1, ih), 760 / max(1, iw))
        shown = pygame.transform.scale(im, (max(1, int(iw*scale)), max(1, int(ih*scale))))
        if alpha != 255:
            shown = shown.copy(); shown.set_alpha(alpha)
        # deterministic-ish shake within a scene: no random sprite identity flicker
        dx = random.randint(-jitter, jitter) if jitter else 0
        dy = random.randint(-jitter, jitter) if jitter else 0
        self.canvas.blit(shown, shown.get_rect(center=(center[0]+dx, center[1]+dy)))

    def current_intro_dialogue_line(self):
        sc = self.intro_scene
        if sc == 1:
            ch = getattr(self,"intro_primary_character",None)
            if ch == "will": return "Всё кончено, Фобос!"
            return "Мы не сдадимся!" if ch else ""
        if sc == 2: return self.intro_second_line
        if sc == 3: return self.intro_phobos_line
        if sc == 5 and not self.intro_transform_all: return self.intro_transform_line
        if sc == 6: return self.intro_final_voice_label
        return ""

    def intro_one_shot(self, tag, sound_name, volume=0.85):
        key = (self.intro_scene, tag)
        if key in self.intro_scene_sfx_played or not self.intro_sfx_channel:
            return
        snd = self.intro_sfx.get(sound_name)
        if snd:
            self.intro_scene_sfx_played.add(key)
            snd.set_volume(volume)
            self.intro_sfx_channel.play(snd)

    def draw_dialogue(self, speaker, line, voiced=False):
        box = pygame.Surface((WINDOW_W-90, 170), pygame.SRCALPHA)
        box.fill((0, 0, 0, 205))
        pygame.draw.rect(box, (150, 90, 190, 230), box.get_rect(), 3)
        self.canvas.blit(box, (45, WINDOW_H-205))
        self.text(speaker, 72, WINDOW_H-185, self.small, COLORS["accent"])
        # v6.15: slower Ace-Attorney-like typewriter, about 15 chars/sec at 60 FPS.
        chars = min(len(line), max(0, self.intro_scene_tick//3))
        shown = line[:chars]
        # Quiet text blip only for unvoiced dialogue. Never compete with recorded speech.
        if not voiced and chars > 0 and chars < len(line) and chars != self.intro_text_last_blip_char and chars % 2 == 0:
            self.intro_text_last_blip_char = chars
            snd = self.intro_sfx.get("text")
            if snd and self.intro_text_channel and not self.intro_text_channel.get_busy():
                snd.set_volume(0.28); self.intro_text_channel.play(snd)
        words, rows, cur = shown.split(), [], ""
        for w in words:
            test = (cur+" "+w).strip()
            if self.font.size(test)[0] > WINDOW_W-155:
                if cur: rows.append(cur)
                cur = w
            else:
                cur = test
        if cur: rows.append(cur)
        for i, row in enumerate(rows[:3]):
            self.text(row, 72, WINDOW_H-145+i*36, self.font)
        self.text("SPACE / ENTER — дальше     X / ESC — пропустить", 72, WINDOW_H-55, self.small, (180,180,195))

    def draw_intro_hall_group(self):
        """Depth-like composition: Phobos farther back, seven heroes closer."""
        self.draw_intro_character("phobos_normal", (WINDOW_W//2, 380), 490, 0)
        positions = {
            "will": (105, 470), "irma": (220, 445), "cornelia": (325, 450),
            "taranee": (545, 450), "haylin": (650, 445), "caleb": (755, 470),
            "blunk": (815, 560),
        }
        for ch, pos in positions.items():
            if self.character_exists(ch):
                self.draw_intro_character(ch+"_normal", pos, 310 if ch != "blunk" else 230, 1)

    def intro_transform_key(self, ch, stage):
        if stage == 0:
            return ch + "_normal"
        if stage == 1:
            return ch + "_t1"
        if stage == 2:
            if ch == "irma" and self.intro_horror_irma and not self.intro_transform_all:
                return "irma_horror"
            return ch + "_t2"
        return ch + "_final"

    def play_intro_final_voice(self):
        if self.intro_voice_played or not self.intro_voice_channel or not self.intro_final_voice_path:
            return
        self.intro_voice_played = True
        try:
            snd = pygame.mixer.Sound(str(self.intro_final_voice_path))
            snd.set_volume(1.0)
            self.intro_voice_channel.play(snd)
            self.music.duck(True)
        except pygame.error:
            pass

    def draw_intro(self):
        sc, t = self.intro_scene, self.intro_scene_tick

        if sc == 0:
            self.intro_play_music("opening")
            self.canvas.fill((0,0,0))
            self.blit_cover(self.intro_images.get("castle"), pygame.Rect(0,0,WINDOW_W,WINDOW_H))
            # Short lightning bursts. A real lightning PNG can later replace this procedural bolt.
            if 35 <= (t % 95) <= 47:
                self.intro_one_shot("castle_lightning", "lightning", 0.80)
                pts=[(random.randint(90, WINDOW_W-90), 0)]; x=pts[0][0]
                for y in range(0, 420, 50):
                    x += random.randint(-35,35); pts.append((x,y))
                pygame.draw.lines(self.canvas, (235,230,255), False, pts, 4)
                flash=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); flash.fill((215,205,255,45)); self.canvas.blit(flash,(0,0))
            title=self.big.render("ЗАМОК ФОБОСА",True,(235,225,255)); self.canvas.blit(title,title.get_rect(center=(WINDOW_W//2,90)))
            return

        self.canvas.fill((0,0,0))
        self.blit_cover(self.intro_images.get("hall"), pygame.Rect(0,0,WINDOW_W,WINDOW_H))

        if sc == 1:
            # Opening speaker must exist in the current world. Will has priority only if enabled.
            ch = getattr(self,"intro_primary_character",None)
            if t < 45:
                self.draw_intro_hall_group()
            elif ch:
                self.draw_intro_character(ch+"_normal", (WINDOW_W//2, 430), 720 if ch != "blunk" else 620, 1)
            line = "Всё кончено, Фобос!" if ch == "will" else "Мы пришли остановить тебя!"
            self.draw_dialogue(self.intro_names.get(ch,""), line)
            return

        if sc == 2:
            # The random second line is always paired with the same character on screen.
            ch = self.intro_second_character
            if ch and self.character_exists(ch):
                self.draw_intro_character(ch+"_normal", (WINDOW_W//2, 430), 720 if ch != "blunk" else 620, 1)
                self.draw_dialogue(self.intro_names[ch], self.intro_second_line)
            else:
                self.draw_intro_character("phobos_normal", (WINDOW_W//2,430),740,1)
            return

        if sc == 3:
            # Phobos begins normal, switches to the casting pose near the end of the line.
            key = "phobos_normal" if t < 105 else "phobos_cast"
            self.draw_intro_character(key, (WINDOW_W//2, 430), 740, 1)
            self.draw_dialogue("ФОБОС", self.intro_phobos_line)
            return

        if sc == 4:
            self.intro_play_music("transformation")
            self.intro_one_shot("cast_lightning", "lightning", 0.92)
            self.intro_one_shot("cast_magic", "magic1", 0.70)
            # Casting beat: lightning, purple flash and screen shake impression.
            self.draw_intro_character("phobos_cast", (WINDOW_W//2 + random.randint(-3,3), 430+random.randint(-3,3)), 750, 2)
            if t % 18 < 6:
                flash=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); flash.fill((230,190,255,105)); self.canvas.blit(flash,(0,0))
            for base_x in (185, WINDOW_W-185):
                x=base_x; pts=[(x,20)]
                for y in range(20,520,70):
                    x += random.randint(-35,35); pts.append((x,y))
                pygame.draw.lines(self.canvas,(225,210,255),False,pts,3)
            return

        if sc == 5:
            self.intro_play_music("transformation")
            self.intro_one_shot("transform_drone", "drone", 0.55)
            self.intro_one_shot("transform_magic", "magic2", 0.62)
            veil=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); veil.fill((35,0,55,115)); self.canvas.blit(veil,(0,0))
            # Four visual stages inside one scene: normal -> t1 -> t2 -> real tetromino.
            stage = 0 if t < 32 else 1 if t < 78 else 2 if t < 132 else 3
            if self.intro_transform_all:
                positions = {
                    "will":(105,390), "irma":(220,500), "cornelia":(335,390), "taranee":(455,500),
                    "haylin":(575,390), "caleb":(700,500), "blunk":(810,400)
                }
                for ch,pos in positions.items():
                    if not self.character_exists(ch): continue
                    key=self.intro_transform_key(ch,stage)
                    self.draw_intro_character(key,pos,265 if ch != "blunk" else 220, 3 if stage in (1,2) else 1)
            else:
                ch=self.intro_transform_character
                if ch and self.character_exists(ch):
                    key=self.intro_transform_key(ch,stage)
                    self.draw_intro_character(key,(WINDOW_W//2,430),720 if ch != "blunk" else 650,3 if stage in (1,2) else 1)
                    self.draw_dialogue(self.intro_names[ch], self.intro_transform_line)
            if t % 23 < 5:
                flash=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); flash.fill((225,190,255,80)); self.canvas.blit(flash,(0,0))
            return

        if sc == 6:
            self.intro_play_music("aftermath")
            self.draw_intro_character("phobos_normal", (WINDOW_W//2,430), 740, 1)
            self.play_intro_final_voice()
            if self.intro_final_voice_label:
                self.draw_dialogue("ФОБОС", self.intro_final_voice_label, voiced=True)
            # restore music volume when the line is over
            if self.intro_voice_channel and not self.intro_voice_channel.get_busy():
                self.music.duck(False)
            return

        # Final title is intentionally not spoken by Phobos.
        self.intro_play_music("aftermath")
        self.intro_one_shot("title_hit", "ominous", 0.82)
        veil=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); veil.fill((0,0,0,145)); self.canvas.blit(veil,(0,0))
        title=self.big.render("ИГРА НАЧАЛАСЬ",True,(205,55,75))
        shadow=self.big.render("ИГРА НАЧАЛАСЬ",True,(35,0,8))
        r=title.get_rect(center=(WINDOW_W//2,WINDOW_H//2))
        self.canvas.blit(shadow,(r.x+3,r.y+3)); self.canvas.blit(title,r)
        self.text("SPACE / ENTER",WINDOW_W//2-90,WINDOW_H//2+75,self.small,(235,235,245))

    # ---------------- v6.31 COLLECTION / MINIGAMES ----------------
    def open_collection(self):
        self.mode="collection"; self.collection_page="root"; self.collection_item_index=0
        self.collection_audio_item=None
        if pygame.mixer.get_init(): pygame.mixer.music.stop()
        self.music.set_phase(-1, force=True)

    def gallery_for(self, category):
        self.collection_gallery_parent=self.collection_page
        roots=[]
        if category=="ACTION POSES":
            files=[
                LINES100_DIR/"will_action.png",
                ASSET_DIR/"minigames"/"irma_face.png",
                LINES100_DIR/"taranee_action.png",
                LINES100_DIR/"cornelia_action.png",
                LINES100_DIR/"haylin_action.png",
                LINES100_DIR/"caleb_action.png",
                ASSET_DIR/"minigames"/"blunk_face.png",
                LINES100_DIR/"phobos_action.png",
            ]
            files=[fp for fp in files if fp.exists()]
        elif category=="TRANSFORMATIONS": roots=[self.intro_processed_dir]
        elif category=="HORROR TETROMINOES":
            root=ASSET_DIR/"sprites"/"horror"
            files=[root/f"{kind}_rotation_0.png" for kind in ("I","O","T","S","Z","J","L")]
            files=[fp for fp in files if fp.exists()]
        elif category=="PHOBOS ROOM STATES": roots=[PHOBOS_ROOM_DIR/"states"]
        elif category=="MERIDIAN WINDOWS": roots=[PHOBOS_ROOM_DIR]
        elif category=="FAILED / UNUSED ART": roots=[ASSET_DIR/"sprites"/"horror_sources"]
        elif category=="SCREENSHOTS": roots=[ASSET_DIR/"development"/"screenshots"]
        if category not in ("ACTION POSES","HORROR TETROMINOES"):
            files=[]
        for root in roots:
            if root.exists():
                for fp in sorted(root.rglob('*')):
                    if fp.is_file() and fp.suffix.lower() in ('.png','.jpg','.jpeg','.webp'):
                        if category=="MERIDIAN WINDOWS" and 'meridian_windows' not in fp.name: continue
                        files.append(fp)
        self.collection_gallery_files=files
        self.collection_gallery_title=category
        self.collection_page="GALLERY"; self.collection_item_index=0

    def collection_current_items(self):
        if self.collection_page == "CUTSCENES": return ["INTRO / OPENING", "100 LINES — RESISTANCE", "200 LINES — CINEMATIC", "PHOBOS ROOM", "BACK"]
        if self.collection_page == "MINIGAMES": return self.minigame_names + ["BACK"]
        if self.collection_page == "AUDIO": return ["MENU — TRACK 1", "MENU — TRACK 2", "INTRO MUSIC", "PHOBOS 0–99 — ARROGANT PRINCE", "PHOBOS ROOM — DARK THEME", "PHOBOS 200+ — MAIN THEME", "PHASE 2 — TRACK 1", "PHASE 2 — TRACK 2", "PHASE 2 — TRACK 3", "WITCH ENDING", "MINIGAMES MUSIC 1", "MINIGAMES MUSIC 2", "MINIGAMES — FOR ARCADE", "VTD — TRACK 1", "VTD — TRACK 2", "STOP", "BACK"]
        if self.collection_page == "ART & SPRITES": return ["ACTION POSES", "HORROR TETROMINOES", "PHOBOS ROOM STATES", "MERIDIAN WINDOWS", "BACK"]
        if self.collection_page == "DEVELOPMENT ARCHIVE": return ["FAILED / UNUSED ART", "SCREENSHOTS", "FACTS & NOTES", "BACK"]
        if self.collection_page == "GALLERY": return [fp.name for fp in self.collection_gallery_files] + ["BACK"]
        return self.collection_sections

    def collection_rects(self):
        items=self.collection_current_items()
        if self.collection_page=="GALLERY":
            start=max(0,min(self.collection_item_index-9,max(0,len(items)-19)))
            return [pygame.Rect(48,150+(i-start)*38,430,34) if start<=i<start+19 else pygame.Rect(-9999,-9999,1,1) for i in range(len(items))]
        return [pygame.Rect(48,169+i*48,800,42) for i in range(len(items))]

    def collection_activate(self):
        items=self.collection_current_items(); item=items[self.collection_item_index]
        if item=="BACK":
            if self.collection_page=="root": self.mode="menu"
            elif self.collection_page=="GALLERY": self.collection_page=self.collection_gallery_parent; self.collection_item_index=0
            else: self.collection_page="root"; self.collection_item_index=0
            return
        if self.collection_page=="root": self.collection_page=item; self.collection_item_index=0; return
        if self.collection_page=="MINIGAMES": self.start_minigame(item); return
        if self.collection_page=="CUTSCENES":
            self.collection_cutscene=True
            if item.startswith("INTRO"):
                self.restart_intro()
            elif item.startswith("100"):
                self.start_new_game(); self.collection_cutscene=True; self.lines=100; self.start_story100()
            elif item.startswith("200"):
                self.start_new_game(); self.collection_cutscene=True; self.lines=200; self.story_seen.add(200); self.story_overlay=200; self.story200_stage="cinematic_reverse"; self.story200_tick=0; self.winner_choice=0; self.music.pause()
            elif item.startswith("PHOBOS ROOM"):
                self.start_new_game(); self.collection_cutscene=True; self.phobos_route=True; self.story_winner="phobos"; self.lines=300; self.enter_phobos_room("collection")
            return
        if self.collection_page=="AUDIO": self.play_collection_audio(item); return
        if self.collection_page=="ART & SPRITES": self.gallery_for(item); return
        if self.collection_page=="DEVELOPMENT ARCHIVE":
            if item in ("FAILED / UNUSED ART","SCREENSHOTS"): self.gallery_for(item)
            return

    def handle_collection_key(self,key):
        items=self.collection_current_items()
        if key==pygame.K_UP: self.collection_item_index=(self.collection_item_index-1)%len(items)
        elif key==pygame.K_DOWN: self.collection_item_index=(self.collection_item_index+1)%len(items)
        elif key==pygame.K_ESCAPE:
            if self.collection_page=="root": self.mode="menu"
            elif self.collection_page=="GALLERY": self.collection_page=self.collection_gallery_parent; self.collection_item_index=0
            else: self.collection_page="root"; self.collection_item_index=0
        elif key in (pygame.K_RETURN,pygame.K_SPACE): self.collection_activate()

    def play_collection_audio(self,item):
        if item=="STOP":
            if pygame.mixer.get_init(): pygame.mixer.music.stop()
            self.collection_audio_item=None; return
        mapping={"MENU — TRACK 1":ASSET_DIR/"audio"/"music"/"menu"/"menu_1.mp3","MENU — TRACK 2":ASSET_DIR/"audio"/"music"/"menu"/"menu_2.mp3","INTRO MUSIC":ASSET_DIR/"audio"/"collection"/"intro_music.mp3","MINIGAMES MUSIC 1":ASSET_DIR/"audio"/"collection"/"minigames_1.mp3","MINIGAMES MUSIC 2":ASSET_DIR/"audio"/"collection"/"minigames_2.mp3","MINIGAMES — FOR ARCADE":ASSET_DIR/"audio"/"minigames"/"arcade_6.mp3","PHASE 2 — TRACK 1":ASSET_DIR/"audio"/"collection"/"phase2_1.mp3","PHASE 2 — TRACK 2":ASSET_DIR/"audio"/"collection"/"phase2_2.mp3","PHASE 2 — TRACK 3":ASSET_DIR/"audio"/"collection"/"phase2_3.mp3","WITCH ENDING":ASSET_DIR/"audio"/"collection"/"witch_ending.mp3","PHOBOS 0–99 — ARROGANT PRINCE":ASSET_DIR/"audio"/"music"/"phase_0_99_phobos"/"Arrogant_Prince_of_the_Obsidian_Court.mp3","PHOBOS ROOM — DARK THEME":ASSET_DIR/"audio"/"music"/"phobos_room"/"PhobosthemeDark.mp3","PHOBOS 200+ — MAIN THEME":ASSET_DIR/"audio"/"music"/"phobos_route"/"Phobos_main_theme_3_phase.mp3","VTD — TRACK 1":ASSET_DIR/"audio"/"music"/"secrets"/"vtd"/"vtd_01.mp3","VTD — TRACK 2":ASSET_DIR/"audio"/"music"/"secrets"/"vtd"/"vtd_02.mp3"}
        fp=mapping.get(item,Path("__missing__"))
        if not (fp.exists() and pygame.mixer.get_init()): return
        if self.collection_audio_item==item and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop(); self.collection_audio_item=None; return
        try:
            pygame.mixer.music.stop(); pygame.mixer.music.load(str(fp)); pygame.mixer.music.play(-1); pygame.mixer.music.set_volume(.72); self.collection_audio_item=item
        except pygame.error: self.collection_audio_item=None

    def play_minigame_music(self, name):
        """Start this minigame's music from 0:00. Retry always calls this again."""
        if not pygame.mixer.get_init():
            return
        mgmusic = ASSET_DIR / "audio" / "minigames"
        tracks = []
        if "SNAKE" in name:
            variant = getattr(self, "mg_snake_variant", 0)
            if variant == 0:
                blunk_track = mgmusic / "blunk_snake.mp3"
                tracks = [blunk_track] if blunk_track.exists() else sorted(mgmusic.glob("snake_*.mp3"))
            else:
                # Cedric and Phobos share the normal Snake pool.
                tracks = sorted(mgmusic.glob("snake_*.mp3"))
        elif name == "BLUNK WASHING":
            # Keep the four established Blunk Washing tracks unchanged.
            tracks = sorted(mgmusic.glob("blunk_washing_*.mp3"))
        else:
            # Generic arcade themes rotate through a shuffled bag: every theme
            # is heard once before the bag is shuffled again.
            tracks = sorted(mgmusic.glob("arcade_*.mp3"))
            if not tracks:
                fallback = ASSET_DIR / "audio" / "collection" / "minigames_1.mp3"
                tracks = [fallback] if fallback.exists() else []
            queue = [q for q in getattr(self, "mg_arcade_music_queue", []) if q in tracks]
            if not queue:
                queue = tracks[:]
                random.shuffle(queue)
                last = getattr(self, "mg_arcade_last_track", None)
                if len(queue) > 1 and queue[0] == last:
                    queue[0], queue[1] = queue[1], queue[0]
            fp = queue.pop(0) if queue else None
            self.mg_arcade_music_queue = queue
            self.mg_arcade_last_track = fp
            tracks = [fp] if fp else []
        if not tracks:
            return
        fp = random.choice(tracks)
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(str(fp))
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(.68)
        except pygame.error as exc:
            print(f"[minigame music] {exc}")

    def start_minigame(self,name):
        pygame.mouse.set_visible(False)
        self.mode="minigame"; self.minigame=name; self.mg_score=0; self.mg_tick=0; self.mg_over=False; self.mg_gameover_reason=""
        self.mg_lives=1 if "SNAKE" in name else 3; self.mg_max_lives=self.mg_lives; self.mg_combo=0; self.mg_wave=1; self.mg_level=1; self.mg_objects=[]; self.mg_obstacles=[]
        # Centered safe arena: every minigame mechanic and sprite stays inside this visible playfield.
        self.mg_arena=pygame.Rect(70,145,WINDOW_W-140,760)
        self.mg_player=[500.0,620.0]; self.mg_vel=[0.0,0.0]; self.mg_jump=0.0; self.mg_ground=790
        self.mg_duck_timer=0
        if name=="CALEB RUNNER": self.mg_player=[160.0,790.0]
        if name in ("TARANEE FIRE SHOT","CORNELIA EARTH GARDEN","BLUNK WASHING","IRMA BUBBLE TROUBLE"): self.mg_player=[500.0,805.0]
        self.mg_dir=(1,0); self.mg_next_dir=(1,0)
        self.mg_snake=[(8,10),(7,10),(6,10)]; self.mg_food=(18,10)
        # 50% Blunk, 25% Cedric, 25% Phobos.
        self.mg_snake_variant=random.choices((0,1,2),weights=(50,25,25),k=1)[0]
        self.mg_ball=[500.0,650.0,5.2,-6.2]; self.mg_paddle_x=500.0; self.mg_paddle_w=170
        arena_tuple=(self.mg_arena.left,self.mg_arena.top,self.mg_arena.width,self.mg_arena.height)
        self.mg_bricks=heart_brick_layout(arena_tuple,self.mg_wave)
        self.mg_invaders=taranee_invader_layout(arena_tuple,self.mg_wave); self.mg_enemy_dir=1; self.mg_enemy_shots=[]
        self.mg_bubbles=[[340.0,300.0,3.1,-5.7,48],[660.0,240.0,-3.3,-5.1,48]]
        self.mg_whirl_angle=0.0; self.mg_whirl_mode="PULL"
        self.mg_corruption=0.0
        self.mg_garden_color=0; self.mg_garden_pulse=0; self.mg_garden_mistakes=0; self.mg_garden_streak=0
        # Fixed-position state shared by the v6.37 Game & Watch-style games.
        self.mg_gw_position=0; self.mg_gw_cedric=6; self.mg_gw_carried=0; self.mg_gw_banked=0
        self.mg_gw_safe_until=FPS; self.mg_gw_cover=1; self.mg_gw_lane=2
        self.mg_gw_stored=0
        self.mg_t_board=[[None for _ in range(10)] for _ in range(18)]
        self.mg_t_kind=random.choice(list(PIECES)); self.mg_t_rot=0; self.mg_t_x=3; self.mg_t_y=0
        self.mg_t_next=random.choice(list(PIECES)); self.mg_t_drop=0
        self.mg_maze_w,self.mg_maze_h,self.mg_maze_tunnel_y,self.mg_maze_walls=build_will_maze()
        self.mg_maze_cell=22; self.mg_maze_origin=(122,166)
        self.mg_maze_player=[13,23]; self.mg_maze_dir=(-1,0); self.mg_maze_next=(-1,0)
        homes=((13,15),(14,15),(12,16),(15,16))
        release_frames=(0,FPS*4,FPS*9,FPS*15)
        self.mg_maze_ghosts=[]
        for kind,(gx,gy) in enumerate(homes):
            self.mg_maze_ghosts.append({"x":gx,"y":gy,"kind":kind,"home":(gx,gy),
                                        "dir":(-1,0),"state":"active" if kind==0 else "house",
                                        "release":release_frames[kind]})
        self.mg_maze_house={(x,y) for y in range(14,18) for x in range(12,16)}
        self.mg_fright=0; self.mg_fright_chain=0
        self.reset_will_maze_wave()
        self.play_minigame_music(name)

    def reset_will_maze_wave(self):
        excluded=set(getattr(self,"mg_maze_house",set())) | {tuple(self.mg_maze_player)}
        open_cells={(x,y) for y in range(self.mg_maze_h) for x in range(self.mg_maze_w)
                    if (x,y) not in self.mg_maze_walls and (x,y) not in excluded}
        corners=((1,1),(self.mg_maze_w-2,1),(1,self.mg_maze_h-2),(self.mg_maze_w-2,self.mg_maze_h-2))
        self.mg_power={p for p in corners if p in open_cells}
        self.mg_pellets=open_cells-self.mg_power

    def caleb_player_rect(self, ducking=None):
        if ducking is None:
            ducking=self.mg_duck_timer>0 or pygame.key.get_pressed()[pygame.K_DOWN]
        # The hitbox follows the animated vertical position. It used to stay
        # nailed to the floor, making SPACE change velocity without producing
        # either a visible or physical jump.
        foot_y=int(self.mg_player[1]+25)
        return pygame.Rect(116,foot_y-68,88,68) if ducking else pygame.Rect(122,foot_y-138,76,138)

    def caleb_obstacle_rect(self, obstacle):
        x=int(obstacle[0]); overhead=bool(obstacle[5])
        if overhead:
            return pygame.Rect(x,int(self.mg_ground+25-118),60,34)
        return pygame.Rect(x,int(self.mg_ground+25-obstacle[3]),obstacle[2],obstacle[3])

    def leave_minigame(self):
        pygame.mouse.set_visible(True)
        self.mode="collection"; self.collection_page="MINIGAMES"; self.collection_item_index=max(0,self.minigame_names.index(self.minigame))
        if pygame.mixer.get_init(): pygame.mixer.music.stop()

    def minigame_game_over(self, reason="GAME OVER"):
        if self.mg_over: return
        self.mg_over=True; self.mg_gameover_reason=reason
        # Keep the last frame visible under the overlay and stop gameplay immediately.
        if pygame.mixer.get_init():
            try: pygame.mixer.music.set_volume(.32)
            except pygame.error: pass

    def game_watch_take_hit(self, reason):
        """Remove one life and preserve the endless, score-only game loop."""
        self.mg_lives-=1
        if self.mg_lives<=0:
            self.minigame_game_over(reason)
            return True
        return False

    def handle_minigame_key(self,key):
        if self.mg_over:
            if key in (pygame.K_SPACE,pygame.K_RETURN): self.start_minigame(self.minigame)
            elif key in (pygame.K_ESCAPE,pygame.K_x): self.leave_minigame()
            return
        if key in (pygame.K_ESCAPE,pygame.K_x): self.leave_minigame(); return
        name=self.minigame
        if "SNAKE" in name:
            if key in (pygame.K_1,pygame.K_2,pygame.K_3):
                new_variant={pygame.K_1:0,pygame.K_2:1,pygame.K_3:2}[key]
                if new_variant != self.mg_snake_variant:
                    self.mg_snake_variant=new_variant
                    self.play_minigame_music(name)
            nd={pygame.K_LEFT:(-1,0),pygame.K_RIGHT:(1,0),pygame.K_UP:(0,-1),pygame.K_DOWN:(0,1)}.get(key)
            if nd and nd!=(-self.mg_dir[0],-self.mg_dir[1]): self.mg_next_dir=nd
        elif name=="WILL MAZE":
            nd={pygame.K_LEFT:(-1,0),pygame.K_RIGHT:(1,0),pygame.K_UP:(0,-1),pygame.K_DOWN:(0,1)}.get(key)
            if nd: self.mg_maze_next=nd
        elif name=="HAY LIN FLIGHT":
            if key==pygame.K_SPACE: self.mg_vel[1]=-8.4
        elif name=="CALEB RUNNER":
            if key in (pygame.K_SPACE,pygame.K_UP) and self.mg_player[1]>=self.mg_ground-1: self.mg_vel[1]=-15.5
            if key==pygame.K_DOWN: self.mg_duck_timer=18
        elif name=="HEART BREAKER":
            if key==pygame.K_LEFT: self.mg_paddle_x-=55
            elif key==pygame.K_RIGHT: self.mg_paddle_x+=55
        elif name=="TARANEE FIRE SHOT":
            if key==pygame.K_LEFT: self.mg_player[0]-=42
            elif key==pygame.K_RIGHT: self.mg_player[0]+=42
            elif key==pygame.K_SPACE and sum(1 for o in self.mg_objects if o[2]=="shot")<3: self.mg_objects.append([self.mg_player[0],760.0,"shot"])
        elif name=="CORNELIA EARTH GARDEN":
            if key==pygame.K_LEFT: self.mg_player[0]-=45
            elif key==pygame.K_RIGHT: self.mg_player[0]+=45
            elif key==pygame.K_UP: self.mg_player[1]-=38
            elif key==pygame.K_DOWN: self.mg_player[1]+=38
            elif key in (pygame.K_1,pygame.K_KP1): self.mg_garden_color=0
            elif key in (pygame.K_2,pygame.K_KP2): self.mg_garden_color=1
            elif key in (pygame.K_3,pygame.K_KP3): self.mg_garden_color=2
            elif key==pygame.K_SPACE and self.mg_garden_pulse<=0:
                targets=[o for o in self.mg_objects if o[2]=="vine" and
                         (o[0]-self.mg_player[0])**2+(o[1]-self.mg_player[1])**2 < 110**2]
                if targets:
                    t=min(targets,key=lambda o:(o[0]-self.mg_player[0])**2+(o[1]-self.mg_player[1])**2)
                    vine_color=int(t[3]) if len(t)>3 else 0
                    if vine_color != self.mg_garden_color:
                        # A wrong resonance feeds the vine and pushes its head
                        # closer to the flower line.
                        self.mg_corruption=min(100.0,self.mg_corruption+10+self.mg_level)
                        t[1]-=42+self.mg_level*2
                        self.mg_garden_mistakes+=1; self.mg_garden_streak=0; self.mg_garden_pulse=14
                    else:
                        if len(t)<4: t.append(0)
                        if len(t)<5: t.append(1)
                        if len(t)<6: t.append(t[4])
                        t[4]-=1; self.mg_score+=2; self.mg_garden_pulse=8
                        self.mg_corruption=max(0.0,self.mg_corruption-0.8)
                        if t[4]<=0:
                            strength=max(1,int(t[5])); self.mg_objects.remove(t)
                            self.mg_score+=6+strength*2; self.mg_garden_streak+=1
                            self.mg_corruption=max(0.0,self.mg_corruption-3.5)
                else:
                    # Blindly spamming cleanse is possible, but it costs time
                    # and lets the corruption creep upward.
                    self.mg_corruption=min(100.0,self.mg_corruption+0.8)
                    self.mg_garden_streak=0; self.mg_garden_pulse=5
        elif name=="BLUNK WASHING":
            if key==pygame.K_LEFT: self.mg_player[0]-=48
            elif key==pygame.K_RIGHT: self.mg_player[0]+=48
        elif name=="IRMA BUBBLE TROUBLE":
            if key==pygame.K_LEFT: self.mg_player[0]-=44
            elif key==pygame.K_RIGHT: self.mg_player[0]+=44
            elif key==pygame.K_SPACE and not any(o[2]=="ray" for o in self.mg_objects): self.mg_objects.append([self.mg_player[0],790.0,"ray"])
        elif name=="IRMA WHIRLPOOL":
            if key==pygame.K_LEFT: self.mg_whirl_angle-=.28
            elif key==pygame.K_RIGHT: self.mg_whirl_angle+=.28
            elif key==pygame.K_SPACE: self.mg_whirl_mode="BLAST"
        elif name=="BLUNK TREASURE ESCAPE":
            old=self.mg_gw_position
            if key==pygame.K_LEFT: self.mg_gw_position=max(0,self.mg_gw_position-1)
            elif key==pygame.K_RIGHT: self.mg_gw_position=min(5,self.mg_gw_position+1)
            if self.mg_gw_position==5 and old!=5:
                self.mg_gw_carried=1
            if self.mg_gw_position==0 and old!=0 and self.mg_gw_carried:
                self.mg_gw_banked+=self.mg_gw_carried
                self.mg_score+=10*self.mg_gw_carried
                self.mg_gw_carried=0; self.mg_gw_cedric=6; self.mg_wave+=1
        elif name=="CORNELIA STONE COVERS":
            if key==pygame.K_LEFT: self.mg_gw_cover=max(0,self.mg_gw_cover-1)
            elif key==pygame.K_RIGHT: self.mg_gw_cover=min(3,self.mg_gw_cover+1)
        elif name=="IRMA DARK WATER PANIC":
            if key==pygame.K_LEFT: self.mg_gw_lane=max(0,self.mg_gw_lane-1)
            elif key==pygame.K_RIGHT: self.mg_gw_lane=min(4,self.mg_gw_lane+1)
            elif key==pygame.K_SPACE and self.mg_gw_stored>=3:
                self.mg_score+=15; self.mg_gw_stored=0; self.mg_wave+=1
        elif name=="PHOBOS TETRIS ???":
            def valid(nx,ny,nr):
                for dx,dy in SHAPES[self.mg_t_kind][nr]:
                    x,y=nx+dx,ny+dy
                    if x<0 or x>=10 or y>=18 or (y>=0 and self.mg_t_board[y][x] is not None): return False
                return True
            if key==pygame.K_LEFT and valid(self.mg_t_x-1,self.mg_t_y,self.mg_t_rot): self.mg_t_x-=1
            elif key==pygame.K_RIGHT and valid(self.mg_t_x+1,self.mg_t_y,self.mg_t_rot): self.mg_t_x+=1
            elif key==pygame.K_DOWN and valid(self.mg_t_x,self.mg_t_y+1,self.mg_t_rot): self.mg_t_y+=1
            elif key in (pygame.K_UP,pygame.K_x,pygame.K_z):
                nr=(self.mg_t_rot+1)%4
                if valid(self.mg_t_x,self.mg_t_y,nr): self.mg_t_rot=nr
            elif key==pygame.K_SPACE:
                while valid(self.mg_t_x,self.mg_t_y+1,self.mg_t_rot): self.mg_t_y+=1
                self.mg_t_drop=99
        arena=getattr(self,"mg_arena",pygame.Rect(70,145,WINDOW_W-140,760))
        self.mg_player[0]=max(arena.left+45,min(arena.right-45,self.mg_player[0]))
        if name=="CORNELIA EARTH GARDEN":
            self.mg_player[1]=max(arena.top+240,min(arena.bottom-55,self.mg_player[1]))

    def update_minigame(self):
        if self.mg_over: return
        self.mg_tick+=1; name=self.minigame; self.mg_level=1+self.mg_tick//900
        keys=pygame.key.get_pressed()
        arena=getattr(self,"mg_arena",pygame.Rect(70,145,WINDOW_W-140,760))
        if name in ("HEART BREAKER","TARANEE FIRE SHOT","CORNELIA EARTH GARDEN","BLUNK WASHING","IRMA BUBBLE TROUBLE"):
            dx=(1 if keys[pygame.K_RIGHT] else 0)-(1 if keys[pygame.K_LEFT] else 0)
            if name=="HEART BREAKER": self.mg_paddle_x += dx*9
            else: self.mg_player[0] += dx*8
            self.mg_player[0]=max(arena.left+45,min(arena.right-45,self.mg_player[0]))
            if name=="CORNELIA EARTH GARDEN":
                dy=(1 if keys[pygame.K_DOWN] else 0)-(1 if keys[pygame.K_UP] else 0)
                self.mg_player[1]+=dy*7
                self.mg_player[1]=max(arena.top+240,min(arena.bottom-55,self.mg_player[1]))
        if "SNAKE" in name:
            step=max(3,9-self.mg_level//2)
            if self.mg_tick%step==0:
                self.mg_dir=self.mg_next_dir; hx,hy=self.mg_snake[0]; nx=(hx+self.mg_dir[0])%28; ny=(hy+self.mg_dir[1])%22
                if (nx,ny) in self.mg_snake:
                    self.minigame_game_over("THE SNAKE WAS CAUGHT"); return
                self.mg_snake.insert(0,(nx,ny))
                if (nx,ny)==self.mg_food:
                    self.mg_score+=5
                    free=[(x,y) for y in range(22) for x in range(28) if (x,y) not in self.mg_snake]
                    if free: self.mg_food=random.choice(free)
                else: self.mg_snake.pop()
        elif name=="WILL MAZE":
            if self.mg_fright>0: self.mg_fright-=1
            elif self.mg_fright_chain: self.mg_fright_chain=0
            # Slower, readable motion: Will still has a modest speed advantage.
            if self.mg_tick%9==0:
                current=tuple(self.mg_maze_player)
                turn=will_maze_step(current,self.mg_maze_next,self.mg_maze_walls,self.mg_maze_w,self.mg_maze_h,self.mg_maze_tunnel_y)
                if turn is not None: self.mg_maze_dir=self.mg_maze_next
                dest=will_maze_step(current,self.mg_maze_dir,self.mg_maze_walls,self.mg_maze_w,self.mg_maze_h,self.mg_maze_tunnel_y)
                if dest is not None: self.mg_maze_player=list(dest)
                pos=tuple(self.mg_maze_player)
                if pos in self.mg_pellets: self.mg_pellets.remove(pos); self.mg_score+=1
                if pos in self.mg_power:
                    self.mg_power.remove(pos); self.mg_score+=25; self.mg_fright=FPS*7; self.mg_fright_chain=0
                if not self.mg_pellets and not self.mg_power:
                    self.mg_wave+=1; self.mg_score+=100; self.reset_will_maze_wave()

            px,py=self.mg_maze_player
            ghost_step=max(12,15-min(3,self.mg_wave//3))+(4 if self.mg_fright>0 else 0)
            if self.mg_tick%ghost_step==0:
                dirs=((1,0),(-1,0),(0,1),(0,-1))
                scatter_targets=((self.mg_maze_w-2,1),(1,1),(self.mg_maze_w-2,self.mg_maze_h-2),(1,self.mg_maze_h-2))
                scatter=(self.mg_tick//FPS)%27 < 7
                for ghost in self.mg_maze_ghosts:
                    kind=ghost["kind"]
                    if ghost["state"]=="house" and self.mg_tick>=ghost["release"]:
                        ghost.update({"x":13+kind%2,"y":12,"state":"active","dir":(-1 if kind%2 else 1,0)})
                    gx,gy=ghost["x"],ghost["y"]
                    if ghost["state"]=="house": continue
                    if ghost["state"]=="eyes": target=ghost["home"]
                    elif scatter: target=scatter_targets[kind]
                    elif kind==0: target=(px,py)
                    elif kind==1: target=(px+self.mg_maze_dir[0]*4,py+self.mg_maze_dir[1]*4)
                    elif kind==2:
                        lead=self.mg_maze_ghosts[0]; target=(2*px-lead["x"],2*py-lead["y"])
                    else: target=scatter_targets[kind] if abs(gx-px)+abs(gy-py)<7 else (px,py)
                    candidates=[]
                    for direction in dirs:
                        cell=will_maze_step((gx,gy),direction,self.mg_maze_walls,self.mg_maze_w,self.mg_maze_h,self.mg_maze_tunnel_y)
                        if cell is None: continue
                        if ghost["state"]=="active" and (gx,gy) not in self.mg_maze_house and cell in self.mg_maze_house: continue
                        candidates.append((cell,direction))
                    if not candidates: continue
                    reverse=(-ghost["dir"][0],-ghost["dir"][1])
                    forward=[item for item in candidates if item[1]!=reverse]
                    if forward: candidates=forward
                    if self.mg_fright>0 and ghost["state"]=="active":
                        cell,direction=max(candidates,key=lambda item:abs(item[0][0]-px)+abs(item[0][1]-py)+random.random())
                    else:
                        cell,direction=min(candidates,key=lambda item:abs(item[0][0]-target[0])+abs(item[0][1]-target[1])+random.random()*.2)
                    ghost["x"],ghost["y"]=cell; ghost["dir"]=direction
                    if ghost["state"]=="eyes" and cell==ghost["home"]:
                        ghost["state"]="house"; ghost["release"]=self.mg_tick+FPS*2

            # Collision is checked after either side moves.
            px,py=self.mg_maze_player
            for ghost in self.mg_maze_ghosts:
                if (ghost["x"],ghost["y"])!=(px,py) or ghost["state"] in ("eyes","house"): continue
                if self.mg_fright>0:
                    self.mg_score+=200*(2**min(3,self.mg_fright_chain)); self.mg_fright_chain+=1; ghost["state"]="eyes"
                else:
                    self.mg_lives-=1
                    if self.mg_lives<=0: self.minigame_game_over("WILL WAS CAUGHT"); return
                    self.mg_maze_player=[13,23]; self.mg_maze_dir=(-1,0); self.mg_maze_next=(-1,0)
                    releases=(0,FPS*4,FPS*9,FPS*15)
                    for g in self.mg_maze_ghosts:
                        g["x"],g["y"]=g["home"]; g["state"]="active" if g["kind"]==0 else "house"; g["release"]=self.mg_tick+releases[g["kind"]]
                    return
        elif name=="HAY LIN FLIGHT":
            speed=6.0+min(7.0,self.mg_tick/800.0); self.mg_vel[1]+=.46; self.mg_player[1]+=self.mg_vel[1]
            if self.mg_player[1]<145 or self.mg_player[1]>850: self.minigame_game_over("HAY LIN FELL"); return
            spawn=max(38,78-self.mg_level*3)
            if self.mg_tick%spawn==0:
                prev=self.mg_obstacles[-1][1] if self.mg_obstacles else 500
                center=max(300,min(700,prev+random.randint(-105,105)))
                self.mg_obstacles.append([arena.right-44,center,max(190,270-self.mg_level*7),False])
            for o in self.mg_obstacles[:]:
                o[0]-=speed; gap=o[2]
                if not o[3] and abs(o[0]-self.mg_player[0])<38 and not (o[1]-gap/2<self.mg_player[1]<o[1]+gap/2): self.minigame_game_over("HAY LIN HIT THE CITY"); return
                if o[0]<self.mg_player[0] and not o[3]: o[3]=True; self.mg_score+=1
                if o[0]<arena.left: self.mg_obstacles.remove(o)
        elif name=="CALEB RUNNER":
            speed=9+min(9,self.mg_tick//650); self.mg_vel[1]+=.78; self.mg_player[1]+=self.mg_vel[1]
            if self.mg_player[1]>=self.mg_ground: self.mg_player[1]=self.mg_ground; self.mg_vel[1]=0
            if self.mg_duck_timer>0: self.mg_duck_timer-=1
            spawn=max(42,82-self.mg_level*3)
            if self.mg_tick%spawn==0:
                overhead=random.random()<0.28
                height=34 if overhead else random.choice((38,52,70))
                self.mg_obstacles.append([float(arena.right-60),self.mg_ground,50,height,False,overhead])
            for o in self.mg_obstacles[:]:
                o[0]-=speed
                ducking=self.mg_duck_timer>0 or keys[pygame.K_DOWN]
                if self.caleb_player_rect(ducking).colliderect(self.caleb_obstacle_rect(o)):
                    self.minigame_game_over("CALEB HIT AN OBSTACLE"); return
                if o[0]+o[2]<116 and not o[4]: o[4]=True; self.mg_score+=1
                if o[0]<arena.left: self.mg_obstacles.remove(o)
        elif name=="HEART BREAKER":
            self.mg_paddle_w=max(88,170-self.mg_level*7); self.mg_paddle_x=max(arena.left+12+self.mg_paddle_w/2,min(arena.right-12-self.mg_paddle_w/2,self.mg_paddle_x))
            b=self.mg_ball; b[0]+=b[2]; b[1]+=b[3]
            if b[0]<arena.left+10 or b[0]>arena.right-10: b[2]*=-1; b[0]=max(arena.left+10,min(arena.right-10,b[0]))
            if b[1]<arena.top+20: b[3]=abs(b[3]); b[1]=arena.top+20
            if 795<b[1]<830 and abs(b[0]-self.mg_paddle_x)<self.mg_paddle_w/2+8 and b[3]>0:
                rel=(b[0]-self.mg_paddle_x)/(self.mg_paddle_w/2); speed=min(12.5,(b[2]**2+b[3]**2)**.5+0.18); b[2]=max(-10,min(10,rel*speed*.9)); b[3]=-max(4.2,(speed**2-b[2]**2)**.5)
            for br in self.mg_bricks[:]:
                rx,ry,rw,rh=br
                if rx-9<b[0]<rx+rw+9 and ry-9<b[1]<ry+rh+9:
                    self.mg_bricks.remove(br); b[3]*=-1; self.mg_score+=5; break
            if not self.mg_bricks:
                self.mg_wave+=1; self.mg_score+=100
                self.mg_bricks=heart_brick_layout((arena.left,arena.top,arena.width,arena.height),self.mg_wave)
                b[2]*=1.06; b[3]*=1.06
            if b[1]>895:
                self.mg_lives-=1
                if self.mg_lives<=0: self.minigame_game_over("THE HEART FELL"); return
                self.mg_ball=[500.0,650.0,5.2+self.mg_wave*.25,-6.2-self.mg_wave*.2]
        elif name=="TARANEE FIRE SHOT":
            self.mg_player[1]=805; self.mg_player[0]=max(arena.left+30,min(arena.right-30,self.mg_player[0]))
            for o in self.mg_objects[:]:
                if o[2]!="shot": continue
                o[1]-=14
                hit=None
                for inv in self.mg_invaders:
                    if abs(o[0]-inv[0])<24 and abs(o[1]-inv[1])<20: hit=inv; break
                if hit: self.mg_invaders.remove(hit); self.mg_objects.remove(o); self.mg_score+=5
                elif o[1]<arena.top+12: self.mg_objects.remove(o)
            enemy_step=max(13,30-self.mg_level*2)
            if self.mg_tick%enemy_step==0 and self.mg_invaders:
                edge=any((i[0]>arena.right-28 if self.mg_enemy_dir>0 else i[0]<arena.left+28) for i in self.mg_invaders)
                if edge: self.mg_enemy_dir*=-1; [i.__setitem__(1,i[1]+22) for i in self.mg_invaders]
                else: [i.__setitem__(0,i[0]+14*self.mg_enemy_dir) for i in self.mg_invaders]
            fire_rate=max(18,62-self.mg_level*4)
            if self.mg_invaders and self.mg_tick%fire_rate==0:
                shooter=random.choice(self.mg_invaders); self.mg_enemy_shots.append([shooter[0],shooter[1]+15])
            for sh in self.mg_enemy_shots[:]:
                sh[1]+=7+min(6,self.mg_level*.45)
                if abs(sh[0]-self.mg_player[0])<24 and abs(sh[1]-805)<25: self.mg_lives-=1; self.mg_enemy_shots.remove(sh); 
                elif sh[1]>arena.bottom-12: self.mg_enemy_shots.remove(sh)
            if self.mg_lives<=0: self.minigame_game_over("TARANEE WAS HIT"); return
            if any(inv[1]>755 for inv in self.mg_invaders): self.minigame_game_over("MERIDIAN OVERRAN TARANEE"); return
            if not self.mg_invaders:
                self.mg_wave+=1; self.mg_score+=100
                self.mg_invaders=taranee_invader_layout((arena.left,arena.top,arena.width,arena.height),self.mg_wave); self.mg_enemy_dir=1
        elif name=="CORNELIA EARTH GARDEN":
            # v6.37.1: the garden is now a colour-matching pressure game, not
            # a one-button mower. Vines gain armour, double-spawn and poison
            # the meter continuously as the level rises.
            if self.mg_garden_pulse>0: self.mg_garden_pulse-=1
            spawn=max(16,50-self.mg_level*3)
            if self.mg_tick%spawn==0:
                def add_corrupted_vine():
                    color=random.randrange(3)
                    lane_centers=(arena.left+145,arena.centerx,arena.right-145)
                    x=int(lane_centers[color]+random.randint(-92,92))
                    base_strength=min(4,1+self.mg_level//3)
                    strength=min(4,base_strength+(1 if random.random()<min(.55,.12+self.mg_level*.045) else 0))
                    self.mg_objects.append([x,float(arena.bottom-55),"vine",color,strength,strength])
                add_corrupted_vine()
                if self.mg_level>=3 and random.random()<min(.62,.08+self.mg_level*.055):
                    add_corrupted_vine()
            for o in self.mg_objects[:]:
                if o[2]=="vine": o[1]-=.52+self.mg_level*.08
                if o[1]<arena.top+185:
                    self.minigame_game_over("A CORRUPTED VINE REACHED THE CRITICAL LINE"); return
            vine_count=sum(1 for o in self.mg_objects if o[2]=="vine")
            armoured=sum(1 for o in self.mg_objects if o[2]=="vine" and len(o)>4 and o[4]>1)
            self.mg_corruption+=.002+vine_count*.004+armoured*.003
            if self.mg_corruption>=100: self.minigame_game_over("THE GARDEN WAS CORRUPTED")
        elif name=="BLUNK WASHING":
            spawn=max(12,25-self.mg_level); speed=6+min(8,self.mg_level*.55)
            if self.mg_tick%spawn==0: self.mg_objects.append([random.randint(arena.left+25,arena.right-25),arena.top+20.0,"water" if random.random()<min(.48,.30+self.mg_level*.018) else "treasure"])
            for o in self.mg_objects[:]:
                o[1]+=speed
                # v6.35: collision is the visible Blunk body, not an invisible 110px-wide floor zone.
                # A drop already below him can no longer hurt him. Treasure remains slightly easier to catch.
                hit_x = abs(o[0]-self.mg_player[0]) < (42 if o[2]=="treasure" else 30)
                hit_y = 755 <= o[1] <= 832
                if hit_x and hit_y:
                    if o[2]=="treasure": self.mg_combo+=1; self.mg_score+=5 if self.mg_combo>=10 else 2
                    else:
                        self.mg_combo=0; self.mg_lives-=1
                        if self.mg_lives<=0: self.minigame_game_over("BLUNK GOT SOAKED"); return
                    self.mg_objects.remove(o)
                elif o[1]>arena.bottom-8: self.mg_objects.remove(o)
        elif name=="IRMA BUBBLE TROUBLE":
            for b in self.mg_bubbles[:]:
                b[0]+=b[2]*(1+self.mg_level*.035); b[1]+=b[3]; b[3]+=.30
                if b[0]<arena.left+b[4] or b[0]>arena.right-b[4]: b[2]*=-1; b[0]=max(arena.left+b[4],min(arena.right-b[4],b[0]))
                if b[1]>780: b[1]=780; b[3]=-abs(b[3])*.94
                if abs(b[0]-self.mg_player[0])<b[4]+18 and abs(b[1]-805)<b[4]+18:
                    self.mg_lives-=1; self.mg_bubbles.remove(b)
                    if self.mg_lives<=0: self.minigame_game_over("IRMA WAS HIT BY FIRE"); return
            for r in self.mg_objects[:]:
                if r[2]!="ray": continue
                r[1]-=15; hit=None
                for b in self.mg_bubbles:
                    if (b[0]-r[0])**2+(b[1]-r[1])**2 < (b[4]+10)**2: hit=b; break
                if hit:
                    self.mg_bubbles.remove(hit); size=hit[4]; self.mg_score+=5
                    if size>18:
                        ns=max(14,int(size*.62)); self.mg_bubbles += [[hit[0],hit[1],-4.2,-6.2,ns],[hit[0],hit[1],4.2,-6.2,ns]]
                    self.mg_objects.remove(r)
                elif r[1]<arena.top+12: self.mg_objects.remove(r)
            if not self.mg_bubbles:
                self.mg_wave+=1; count=min(5,2+self.mg_wave//2); self.mg_bubbles=[[random.randint(180,820),random.randint(190,390),random.choice((-3.5,3.5)),-5.5,48] for _ in range(count)]
        elif name=="IRMA WHIRLPOOL":
            # Arrow keys are held controls, not one-step taps.
            self.mg_whirl_angle += .004 + ((1 if keys[pygame.K_RIGHT] else 0)-(1 if keys[pygame.K_LEFT] else 0))*.055
            spawn=max(22,48-self.mg_level*2)
            if self.mg_tick%spawn==0: self.mg_objects.append([385.0,random.uniform(0,6.28),"enemy" if random.random()<.42 else "debris"])
            blasting=self.mg_whirl_mode=="BLAST"
            for o in self.mg_objects[:]:
                o[1]+=.010; o[0]-=1.35+min(2.2,self.mg_level*.11)
                diff=abs((o[1]-self.mg_whirl_angle+math.pi)%(2*math.pi)-math.pi)
                if blasting and diff<.34 and o[0]<360:
                    if o[2]=="enemy": self.mg_score+=5; self.mg_objects.remove(o); continue
                    else: self.mg_lives-=1; self.mg_objects.remove(o)
                elif o[0]<72:
                    if o[2]=="debris": self.mg_score+=3
                    else: self.mg_lives-=1
                    self.mg_objects.remove(o)
                if self.mg_lives<=0: self.minigame_game_over("THE WHIRLPOOL WON"); return
            self.mg_whirl_mode="AIM"
        elif name=="BLUNK TREASURE ESCAPE":
            # Blunk raids a treasure cache and must return to the left before
            # Cedric's canonical serpent form catches him. There is no boat
            # and no final treasure: every delivery starts a faster pursuit.
            chase_step=max(14,54-self.mg_level*4-self.mg_wave)
            if self.mg_tick%chase_step==0:
                if self.mg_gw_cedric>self.mg_gw_position: self.mg_gw_cedric-=1
                elif self.mg_gw_cedric<self.mg_gw_position: self.mg_gw_cedric+=1
            if self.mg_tick>=self.mg_gw_safe_until and self.mg_gw_cedric==self.mg_gw_position:
                lost=self.game_watch_take_hit("CEDRIC CAUGHT BLUNK")
                self.mg_gw_position=0; self.mg_gw_cedric=6; self.mg_gw_carried=0
                self.mg_gw_safe_until=self.mg_tick+FPS
                if lost: return
        elif name=="CORNELIA STONE COVERS":
            spawn=max(28,92-self.mg_level*6)
            if self.mg_tick%spawn==0:
                self.mg_objects.append([random.randrange(4),max(18,58-self.mg_level*3)])
            for traveller in self.mg_objects[:]:
                traveller[1]-=1
                if traveller[1]>0: continue
                self.mg_objects.remove(traveller)
                if traveller[0]==self.mg_gw_cover: self.mg_score+=2
                elif self.game_watch_take_hit("THE MERIDIAN ROAD COLLAPSED"): return
        elif name=="IRMA DARK WATER PANIC":
            # Five fixed lanes make positioning more deliberate. Difficulty
            # rises every 18 seconds: drops arrive more often and fall faster,
            # but the game never inserts a safety pause after filling the vessel.
            irma_level,spawn,speed=irma_dark_water_curve(self.mg_tick)
            if self.mg_tick%spawn==0:
                self.mg_objects.append([random.randrange(5),float(arena.top+25)])
            for drop in self.mg_objects[:]:
                drop[1]+=speed
                if drop[1]<arena.bottom-92: continue
                self.mg_objects.remove(drop)
                if drop[0]==self.mg_gw_lane and self.mg_gw_stored<3:
                    self.mg_gw_stored+=1; self.mg_score+=1
                elif self.game_watch_take_hit("DARK WATER FLOODED MERIDIAN"): return
        elif name=="PHOBOS TETRIS ???":
            def valid(nx,ny,nr):
                for dx,dy in SHAPES[self.mg_t_kind][nr]:
                    x,y=nx+dx,ny+dy
                    if x<0 or x>=10 or y>=18 or (y>=0 and self.mg_t_board[y][x] is not None): return False
                return True
            self.mg_t_drop+=1
            interval=max(5,24-self.mg_level*2)
            if self.mg_t_drop>=interval:
                self.mg_t_drop=0
                if valid(self.mg_t_x,self.mg_t_y+1,self.mg_t_rot): self.mg_t_y+=1
                else:
                    for dx,dy in SHAPES[self.mg_t_kind][self.mg_t_rot]:
                        x,y=self.mg_t_x+dx,self.mg_t_y+dy
                        if y<0: self.minigame_game_over("PHOBOS FILLED THE WELL"); return
                        self.mg_t_board[y][x]=self.mg_t_kind
                    full=[r for r,row in enumerate(self.mg_t_board) if all(v is not None for v in row)]
                    for r in reversed(full): del self.mg_t_board[r]; self.mg_t_board.insert(0,[None]*10)
                    if full: self.mg_score += (100,300,500,800)[min(3,len(full)-1)]; self.mg_corruption+=len(full)*2
                    # Phobos cheats more often with time: repeats NEXT and occasionally changes it. Geometry stays exact.
                    self.mg_t_kind=self.mg_t_next
                    if random.random()<min(.55,.12+self.mg_level*.035): self.mg_t_next=self.mg_t_kind
                    else: self.mg_t_next=random.choice(list(PIECES))
                    self.mg_t_rot=0; self.mg_t_x=3; self.mg_t_y=0
                    if not valid(self.mg_t_x,self.mg_t_y,self.mg_t_rot): self.minigame_game_over("PHOBOS FILLED THE WELL"); return

    def draw_collection(self):
        self.draw_background("menu"); ov=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); ov.fill((5,3,10,225)); self.canvas.blit(ov,(0,0))
        self.text("COLLECTION — TEST BUILD / EVERYTHING UNLOCKED",55,42,self.font,COLORS["accent"])
        self.text(self.collection_gallery_title if self.collection_page=="GALLERY" else self.collection_page,55,88,self.font,COLORS["text"])
        items=self.collection_current_items()
        if self.collection_page=="GALLERY":
            # WINDOW_W is 860: the old 490+465 preview extended 95 pixels past
            # the canvas and was visibly clipped on macOS. Keep a real gutter.
            list_rect=pygame.Rect(42,135,350,805); preview=pygame.Rect(410,135,410,805)
            pygame.draw.rect(self.canvas,(16,10,28),preview); pygame.draw.rect(self.canvas,(100,65,125),preview,2)
            start=max(0,min(self.collection_item_index-9,max(0,len(items)-19)))
            for row,i in enumerate(range(start,min(len(items),start+19))):
                item=items[i]; y=155+row*38
                if i==self.collection_item_index: pygame.draw.rect(self.canvas,(82,42,105),(48,y-4,338,32))
                self.text(("▶ " if i==self.collection_item_index else "  ")+item[:25],58,y,self.small)
            if self.collection_gallery_files and self.collection_item_index < len(self.collection_gallery_files):
                fp=self.collection_gallery_files[self.collection_item_index]
                try:
                    img=load_clean_alpha(fp); iw,ih=img.get_size(); margin=18
                    sc=min((preview.width-2*margin)/max(1,iw),(preview.height-2*margin)/max(1,ih),1.0)
                    shown=pygame.transform.smoothscale(img,(max(1,int(iw*sc)),max(1,int(ih*sc))))
                    old=self.canvas.get_clip(); self.canvas.set_clip(preview.inflate(-6,-6)); self.canvas.blit(shown,shown.get_rect(center=preview.center)); self.canvas.set_clip(old)
                except (pygame.error,ValueError): pass
        else:
            for i,item in enumerate(items):
                y=175+i*48
                if i==self.collection_item_index: pygame.draw.rect(self.canvas,(82,42,105),(48,y-6,800,40))
                suffix=""
                if self.collection_page=="AUDIO" and item==self.collection_audio_item and pygame.mixer.get_init() and pygame.mixer.music.get_busy(): suffix="  [PLAYING]"
                self.text(("▶ " if i==self.collection_item_index else "  ")+item+suffix,62,y,self.small)
        self.text("MOUSE / ↑↓ SELECT   CLICK / SPACE OPEN   ESC BACK",55,970,self.small)

    def draw_minigame(self):
        self.canvas.fill((12,8,22)); self.text(self.minigame,40,28,self.font,COLORS["accent"]); self.text(f"SCORE {self.mg_score}",760,35,self.small); heart_text="♥"*max(0,self.mg_lives)+"♡"*max(0,getattr(self,"mg_max_lives",3)-self.mg_lives)
        hs=self.font.render(heart_text,True,(240,90,125)); self.canvas.blit(hs,hs.get_rect(center=(WINDOW_W//2,70))); self.text("ESC / X — BACK",40,72,self.small)
        arena=getattr(self,"mg_arena",pygame.Rect(70,145,WINDOW_W-140,760)); pygame.draw.rect(self.canvas,(27,16,42),arena); pygame.draw.rect(self.canvas,(125,75,150),arena,3)
        old_clip=self.canvas.get_clip(); self.canvas.set_clip(arena.inflate(-3,-3)); n=self.minigame
        def mg_sprite(key, center, max_w=80, max_h=90):
            src=self.mg_art.get(key)
            if not src: return False
            sc=min(max_w/src.get_width(),max_h/src.get_height())
            im=pygame.transform.smoothscale(src,(max(1,int(src.get_width()*sc)),max(1,int(src.get_height()*sc))))
            self.canvas.blit(im,im.get_rect(center=(int(center[0]),int(center[1])))); return True
        if "SNAKE" in n:
            cw,ch=arena.width//28,arena.height//22
            variant=getattr(self,"mg_snake_variant",0)
            head_key=("blunk_face","cedric_face","phobos_face")[variant]
            body_col=((245,195,40),(70,170,80),(18,14,24))[variant]
            for i,(x,y) in enumerate(self.mg_snake):
                rr=pygame.Rect(arena.x+x*cw,arena.y+y*ch,cw-2,ch-2)
                if i==0 and head_key in self.mg_art:
                    img=self.mg_art[head_key]; sc=min(rr.width/img.get_width(),rr.height/img.get_height())*1.45; sh=pygame.transform.smoothscale(img,(max(1,int(img.get_width()*sc)),max(1,int(img.get_height()*sc)))); self.canvas.blit(sh,sh.get_rect(center=rr.center))
                else: pygame.draw.rect(self.canvas,body_col,rr)
            x,y=self.mg_food
            self.text(("1 BLUNK   2 CEDRIC   3 PHOBOS   NOW: "+("BLUNK","CEDRIC","PHOBOS")[variant]),65,125,self.small)
            food_rect=pygame.Rect(arena.x+x*cw,arena.y+y*ch,cw-2,ch-2)
            if variant==2 and "heart_kandrakar" in self.mg_art:
                img=self.mg_art["heart_kandrakar"]; sc=min(food_rect.width/img.get_width(),food_rect.height/img.get_height())*.92; sh=pygame.transform.smoothscale(img,(max(1,int(img.get_width()*sc)),max(1,int(img.get_height()*sc)))); self.canvas.blit(sh,sh.get_rect(center=food_rect.center))
            elif variant==1 and "phobos_face" in self.mg_art:
                # Cedric's food is literally Phobos, not an abstract sphere.
                img=self.mg_art["phobos_face"]; sc=min(food_rect.width/img.get_width(),food_rect.height/img.get_height())*1.15; sh=pygame.transform.smoothscale(img,(max(1,int(img.get_width()*sc)),max(1,int(img.get_height()*sc)))); self.canvas.blit(sh,sh.get_rect(center=food_rect.center))
            else:
                pygame.draw.circle(self.canvas,(250,215,55),food_rect.center,8)
        elif n=="WILL MAZE":
            ox,oy=self.mg_maze_origin; c=self.mg_maze_cell
            for x,y in self.mg_maze_walls: pygame.draw.rect(self.canvas,(74,47,110),(ox+x*c,oy+y*c,c,c))
            for x,y in self.mg_pellets: pygame.draw.circle(self.canvas,(220,210,225),(ox+x*c+c//2,oy+y*c+c//2),3)
            for x,y in self.mg_power:
                hc=(ox+x*c+c//2,oy+y*c+c//2)
                if not mg_sprite("heart_kandrakar",hc,22,22): pygame.draw.circle(self.canvas,(255,235,150),hc,8)
            px,py=self.mg_maze_player; pc=(ox+px*c+c//2,oy+py*c+c//2)
            if not mg_sprite("will_face",pc,c-3,c-3): pygame.draw.circle(self.canvas,(245,185,230),pc,13)
            cols=[(230,70,80),(240,150,90),(80,170,230),(150,95,185)]
            for ghost in self.mg_maze_ghosts:
                gx,gy,k=ghost["x"],ghost["y"],ghost["kind"]
                gc=(ox+gx*c+c//2,oy+gy*c+c//2)
                shown=mg_sprite(f"will_enemy_{k+1}",gc,c-2,c-2)
                if not shown: pygame.draw.circle(self.canvas,cols[k],gc,max(5,c//2-1))
                if ghost["state"]=="eyes":
                    pygame.draw.circle(self.canvas,(235,245,255),gc,max(5,c//2-2),2)
                    pygame.draw.circle(self.canvas,(80,120,220),(gc[0]-3,gc[1]),2); pygame.draw.circle(self.canvas,(80,120,220),(gc[0]+3,gc[1]),2)
                elif self.mg_fright>0 and ghost["state"]=="active":
                    pygame.draw.circle(self.canvas,(105,165,245),gc,max(6,c//2),3)
        elif n=="HAY LIN FLIGHT":
            if "haylin_bg" in self.mg_art:
                bg=pygame.transform.smoothscale(self.mg_art["haylin_bg"],arena.size); self.canvas.blit(bg,arena.topleft)
            if "haylin_flight" in self.mg_art:
                src=self.mg_art["haylin_flight"]; h=90; w=max(1,int(src.get_width()*h/src.get_height())); im=pygame.transform.smoothscale(src,(w,h)); self.canvas.blit(im,im.get_rect(center=(int(self.mg_player[0]),int(self.mg_player[1]))))
            else: pygame.draw.circle(self.canvas,(180,225,245),(int(self.mg_player[0]),int(self.mg_player[1])),22)
            for x,gap,gapsz,_ in self.mg_obstacles:
                top=max(0,int(gap-gapsz/2-arena.y)); bottom=int(gap+gapsz/2)
                # Dark magic cloud columns replace the old tower/fence blocks.
                for cy in range(arena.y+12,arena.y+top,20):
                    pygame.draw.circle(self.canvas,(54,35,78),(int(x)+22,cy),26)
                    pygame.draw.circle(self.canvas,(92,50,116),(int(x)+10,cy+7),17)
                for cy in range(bottom+12,arena.bottom,20):
                    pygame.draw.circle(self.canvas,(54,35,78),(int(x)+22,cy),26)
                    pygame.draw.circle(self.canvas,(92,50,116),(int(x)+34,cy-6),17)
            self.text("SPACE — FLAP",65,125,self.small)
        elif n=="CALEB RUNNER":
            pygame.draw.line(self.canvas,(150,120,120),(arena.left,self.mg_ground+25),(arena.right,self.mg_ground+25),4)
            ducking=self.mg_duck_timer>0 or pygame.key.get_pressed()[pygame.K_DOWN]
            pr=self.caleb_player_rect(ducking); src=self.mg_art.get("caleb")
            if src:
                target=(88,68) if ducking else (120,138)
                im=pygame.transform.smoothscale(src,target); self.canvas.blit(im,im.get_rect(midbottom=(160,int(self.mg_player[1]+25))))
            else: pygame.draw.rect(self.canvas,(165,115,80),pr)
            for o in self.mg_obstacles:
                pygame.draw.rect(self.canvas,(130,80,70),self.caleb_obstacle_rect(o))
            self.text("SPACE/UP — JUMP   DOWN — DUCK",65,125,self.small)
        elif n=="HEART BREAKER":
            for x,y,w,h in self.mg_bricks:
                r=pygame.Rect(x,y,w,h); pygame.draw.rect(self.canvas,(92,82,86),r); pygame.draw.rect(self.canvas,(145,128,126),r,2)
                pygame.draw.line(self.canvas,(45,37,42),(r.x+18,r.y+2),(r.x+29,r.y+13),2); pygame.draw.line(self.canvas,(45,37,42),(r.x+29,r.y+13),(r.x+23,r.bottom-2),2); pygame.draw.line(self.canvas,(45,37,42),(r.x+29,r.y+13),(r.x+43,r.y+7),2)
            pygame.draw.rect(self.canvas,(225,185,240),(int(self.mg_paddle_x-self.mg_paddle_w/2),810,int(self.mg_paddle_w),18)); pygame.draw.circle(self.canvas,(250,220,245),(int(self.mg_ball[0]),int(self.mg_ball[1])),10)
            self.text(f"WAVE {self.mg_wave}   LEFT/RIGHT — PADDLE",65,125,self.small)
        elif n=="TARANEE FIRE SHOT":
            for x,y in self.mg_invaders: pygame.draw.rect(self.canvas,(205,85,75),(int(x-18),int(y-14),36,28))
            mg_sprite("taranee",(int(self.mg_player[0]),790),130,155)
            for x,y,k in self.mg_objects:
                if k=="shot": pygame.draw.rect(self.canvas,(255,190,90),(int(x-3),int(y-12),6,24))
            for x,y in self.mg_enemy_shots: pygame.draw.circle(self.canvas,(205,70,190),(int(x),int(y)),7)
            self.text(f"WAVE {self.mg_wave}   LEFT/RIGHT + SPACE — FIRE",65,125,self.small)
        elif n=="CORNELIA EARTH GARDEN":
            critical=arena.top+185
            pygame.draw.line(self.canvas,(170,55,85),(arena.left,critical),(arena.right,critical),3)
            pygame.draw.rect(self.canvas,(55,85,48),(arena.x,760,arena.width,max(0,arena.bottom-760)))
            garden_colors=((225,72,92),(80,155,245),(238,190,65))
            garden_names=("CRIMSON","AZURE","GOLD")
            flower_x=(arena.left+145,arena.centerx,arena.right-145)
            for index,flower_center in enumerate(flower_x):
                color=garden_colors[index]
                pygame.draw.line(self.canvas,(75,135,70),(flower_center,critical+28),(flower_center,critical+72),5)
                for angle in range(0,360,72):
                    px=flower_center+int(math.cos(math.radians(angle))*13)
                    py=critical+23+int(math.sin(math.radians(angle))*13)
                    pygame.draw.circle(self.canvas,color,(px,py),9)
                pygame.draw.circle(self.canvas,(235,215,115),(flower_center,critical+23),7)
            mg_sprite("cornelia",(int(self.mg_player[0]),int(self.mg_player[1])),130,165)
            if self.mg_garden_pulse>0:
                pygame.draw.circle(self.canvas,garden_colors[self.mg_garden_color],
                                   (int(self.mg_player[0]),int(self.mg_player[1]-70)),112,4)
            for vine in self.mg_objects:
                x,y,k=vine[:3]
                color_index=int(vine[3]) if len(vine)>3 else 0
                hp=int(vine[4]) if len(vine)>4 else 1
                max_hp=int(vine[5]) if len(vine)>5 else hp
                vine_color=garden_colors[color_index%len(garden_colors)]
                pygame.draw.line(self.canvas,(102,45,118),(int(x),arena.bottom-32),(int(x),int(y)),6)
                for ty in range(int(y)+20,arena.bottom-40,42):
                    side=-1 if (ty//42)%2 else 1
                    pygame.draw.polygon(self.canvas,(86,33,98),[(int(x),ty),(int(x)+side*12,ty-7),(int(x),ty+5)])
                pygame.draw.circle(self.canvas,(65,20,65),(int(x),int(y)),17)
                pygame.draw.circle(self.canvas,vine_color,(int(x),int(y)),12)
                for hit in range(max_hp):
                    pip=(245,235,250) if hit<hp else (65,45,70)
                    pygame.draw.rect(self.canvas,pip,(int(x)-max_hp*6+hit*12,int(y)-28,8,5))
            selected=garden_names[self.mg_garden_color]
            self.text(f"CORRUPTION {int(self.mg_corruption)}%   STREAK {self.mg_garden_streak}   RESONANCE {selected}",85,160,self.small)
            self.text("ARROWS — MOVE   1/2/3 — COLOUR   SPACE — CLEANSE",85,184,self.small)
        elif n=="BLUNK WASHING":
            if "blunk_face" in self.mg_art:
                src=self.mg_art["blunk_face"]; h=92; w=max(1,int(src.get_width()*h/src.get_height())); im=pygame.transform.smoothscale(src,(w,h)); self.canvas.blit(im,im.get_rect(center=(int(self.mg_player[0]),800)))
            else:
                pygame.draw.circle(self.canvas,(125,175,70),(int(self.mg_player[0]),800),38)
            for x,y,k in self.mg_objects: pygame.draw.circle(self.canvas,(70,155,235) if k=="water" else (250,205,70),(int(x),int(y)),14)
            self.text(f"COMBO {self.mg_combo}   CATCH GOLD / AVOID WATER",65,125,self.small)
        elif n=="IRMA BUBBLE TROUBLE":
            mg_sprite("irma_face",(int(self.mg_player[0]),795),78,90)
            for x,y,vx,vy,size in self.mg_bubbles: pygame.draw.circle(self.canvas,(245,105,45),(int(x),int(y)),int(size)); pygame.draw.circle(self.canvas,(255,210,70),(int(x),int(y)),max(4,int(size*.45)))
            for x,y,k in self.mg_objects:
                if k=="ray": pygame.draw.line(self.canvas,(160,220,255),(int(x),int(y)),(int(x),805),4)
            self.text(f"WAVE {self.mg_wave}   LEFT/RIGHT + SPACE — EXTINGUISH FIRE",65,125,self.small)
        elif n=="IRMA WHIRLPOOL":
            cx,cy=WINDOW_W//2,520; pygame.draw.circle(self.canvas,(80,150,220),(cx,cy),70,4); mg_sprite("irma_face",(cx,cy),62,70)
            ex=cx+math.cos(self.mg_whirl_angle)*155; ey=cy+math.sin(self.mg_whirl_angle)*155; pygame.draw.line(self.canvas,(160,225,255),(cx,cy),(int(ex),int(ey)),4)
            for rad,ang,k in self.mg_objects:
                x=cx+math.cos(ang)*rad; y=cy+math.sin(ang)*rad
                orb_color=(230,80,100) if k=="enemy" else (70,165,245)
                pygame.draw.circle(self.canvas,orb_color,(int(x),int(y)),12)
                if k!="enemy": pygame.draw.circle(self.canvas,(175,225,255),(int(x)-3,int(y)-3),4)
            self.text("LEFT/RIGHT — AIM WATER   SPACE — BLAST RED HAZARDS",65,125,self.small)
        elif n=="BLUNK TREASURE ESCAPE":
            xs=[130+i*105 for i in range(7)]; track_y=690
            pygame.draw.line(self.canvas,(104,78,55),(xs[0],track_y+42),(xs[5],track_y+42),8)
            for x in xs[:6]:
                pygame.draw.circle(self.canvas,(195,160,90),(x,track_y+42),10)
            # The cache replaces the mistakenly proposed boat. Blunk must
            # steal one object and escape left while serpent-Cedric pursues.
            chest=pygame.Rect(xs[5]-42,track_y-12,84,58)
            pygame.draw.rect(self.canvas,(112,62,32),chest); pygame.draw.rect(self.canvas,(224,178,66),chest,5)
            pygame.draw.circle(self.canvas,(250,220,85),(xs[5],track_y+16),8)
            bx=xs[self.mg_gw_position]
            mg_sprite("blunk_face",(bx,track_y-35),82,82)
            if self.mg_gw_carried: pygame.draw.circle(self.canvas,(255,220,70),(bx+30,track_y-58),10)
            cx=xs[min(6,self.mg_gw_cedric)]
            for seg in range(7,-1,-1):
                sx=min(arena.right-8,cx+seg*20); sy=track_y-15+int(math.sin(seg*.9)*18)
                pygame.draw.circle(self.canvas,(50,92,58),(sx,sy),24)
                pygame.draw.arc(self.canvas,(205,55,48),(sx-24,sy-24,48,48),0,math.pi,5)
            mg_sprite("cedric_face",(min(arena.right-58,cx),track_y-92),105,112)
            self.text(f"TREASURE {self.mg_gw_banked}   CARRIED {self.mg_gw_carried}",65,125,self.small)
            self.text("LEFT/RIGHT — RAID THE CACHE AND ESCAPE CEDRIC",130,850,self.small)
        elif n=="CORNELIA STONE COVERS":
            xs=[155+i*180 for i in range(4)]; road_y=680
            pygame.draw.rect(self.canvas,(82,70,75),(arena.left+15,road_y-25,arena.width-30,125))
            guardian_keys=("will_face","irma_face","taranee_face","haylin_face")
            for i,x in enumerate(xs):
                pygame.draw.circle(self.canvas,(35,25,42),(x,road_y+27),48)
                pygame.draw.circle(self.canvas,(150,110,165),(x,road_y+27),49,3)
                mg_sprite(guardian_keys[i],(x,road_y+24),78,82)
                if i==self.mg_gw_cover:
                    shield=pygame.Rect(x-57,road_y-42,114,116)
                    pygame.draw.arc(self.canvas,(205,180,145),shield,math.pi,2*math.pi,10)
                    pygame.draw.ellipse(self.canvas,(133,114,105),(x-55,road_y+57,110,22))
                    pygame.draw.ellipse(self.canvas,(205,180,145),(x-55,road_y+57,110,22),4)
            for lane,remaining in self.mg_objects:
                y=max(arena.top+90,road_y-80-int(remaining)*5)
                pygame.draw.circle(self.canvas,(232,202,166),(xs[lane],y),20)
                pygame.draw.line(self.canvas,(232,202,166),(xs[lane],y+20),(xs[lane],y+55),7)
            mg_sprite("cornelia",(WINDOW_W//2,390),165,225)
            self.text("LEFT/RIGHT — MOVE THE EARTH COVER",205,850,self.small)
        elif n=="IRMA DARK WATER PANIC":
            xs=(130,280,430,580,730)
            for x in xs: pygame.draw.line(self.canvas,(50,70,95),(x,arena.top+25),(x,arena.bottom-90),2)
            for lane,y in self.mg_objects:
                x=xs[int(lane)]; pygame.draw.circle(self.canvas,(85,35,125),(x,int(y)),15)
                pygame.draw.circle(self.canvas,(145,70,190),(x-4,int(y)-5),5)
            ix=xs[self.mg_gw_lane]
            mg_sprite("irma_face",(ix,760),82,92)
            vessel=pygame.Rect(ix-42,798,84,55)
            pygame.draw.rect(self.canvas,(65,125,175),vessel,4)
            fill=int(47*self.mg_gw_stored/3)
            if fill: pygame.draw.rect(self.canvas,(74,35,115),(vessel.x+7,vessel.bottom-7-fill,vessel.width-14,fill))
            # Dumped corruption lands on Phobos's guards below the ledge.
            for gx in (330,530):
                pygame.draw.circle(self.canvas,(75,55,62),(gx,875),20); pygame.draw.rect(self.canvas,(82,60,68),(gx-18,888,36,25))
            irma_level,_,_=irma_dark_water_curve(self.mg_tick)
            self.text(f"VESSEL {self.mg_gw_stored}/3   LANE {self.mg_gw_lane+1}/5   LEVEL {irma_level}",130,125,self.small)
            self.text("LEFT/RIGHT — CATCH   SPACE — DUMP AT 3",205,850,self.small)
        else:
            bx,by,cs=330,175,34
            pygame.draw.rect(self.canvas,(5,5,8),(bx,by,10*cs,18*cs)); pygame.draw.rect(self.canvas,(100,90,105),(bx,by,10*cs,18*cs),2)
            for yy,row in enumerate(self.mg_t_board):
                for xx,k in enumerate(row):
                    if k is not None: pygame.draw.rect(self.canvas,PIECE_COLORS.get(k,(180,180,180)),(bx+xx*cs+1,by+yy*cs+1,cs-2,cs-2))
            for dx,dy in SHAPES[self.mg_t_kind][self.mg_t_rot]: pygame.draw.rect(self.canvas,PIECE_COLORS.get(self.mg_t_kind,(220,220,220)),(bx+(self.mg_t_x+dx)*cs+1,by+(self.mg_t_y+dy)*cs+1,cs-2,cs-2))
            self.text(f"NEXT: {self.mg_t_next}   PHOBOS MAY CHEAT — GEOMETRY DOES NOT",65,125,self.small)
        self.canvas.set_clip(old_clip)
        if self.mg_over:
            shade=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); shade.fill((0,0,0,205)); self.canvas.blit(shade,(0,0))
            box=pygame.Rect(230,325,540,350); pygame.draw.rect(self.canvas,(26,12,38),box); pygame.draw.rect(self.canvas,(180,105,185),box,4)
            t=self.big.render("GAME OVER",True,(240,190,230)); self.canvas.blit(t,t.get_rect(center=(WINDOW_W//2,390)))
            why=self.small.render(self.mg_gameover_reason,True,COLORS["text"]); self.canvas.blit(why,why.get_rect(center=(WINDOW_W//2,470)))
            sc=self.font.render(f"SCORE: {self.mg_score}",True,COLORS["accent"]); self.canvas.blit(sc,sc.get_rect(center=(WINDOW_W//2,525)))
            self.text("SPACE / ENTER — RETRY",335,585,self.small); self.text("ESC / X — COLLECTION",335,625,self.small)

    def draw_splash(self):
        self.draw_background("menu")
        veil = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 125))
        self.canvas.blit(veil, (0, 0))
        title = self.big.render("W.I.T.C.H. TETRIS", True, COLORS["accent"])
        self.canvas.blit(title, title.get_rect(center=(WINDOW_W//2, WINDOW_H//2-55)))
        sub = self.font.render("THE SPELL OF PHOBOS", True, COLORS["text"])
        self.canvas.blit(sub, sub.get_rect(center=(WINDOW_W//2, WINDOW_H//2+10)))
        blink = (self.menu_tick//35) % 2 == 0
        if blink:
            press = self.small.render("SPACE / ENTER", True, COLORS["text"])
            self.canvas.blit(press, press.get_rect(center=(WINDOW_W//2, WINDOW_H//2+95)))

    def draw_menu(self):
        self.draw_background("menu")
        # Left menu slab. The right edge is intentionally placed under Phobos's elbow.
        panel_rect = pygame.Rect(50, 245, 650, 540)
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel.fill((10, 8, 18, 220))
        pygame.draw.rect(panel, (110, 74, 130, 255), panel.get_rect(), 3)
        self.canvas.blit(panel, panel_rect.topleft)
        self.text("W.I.T.C.H. TETRIS", 88, 285, self.font, COLORS["accent"])
        self.text("PHOBOS' PALACE", 88, 330, self.small)
        for i, item in enumerate(self.menu_items):
            y = 400 + i*72
            selected = i == self.menu_index
            if selected:
                pygame.draw.rect(self.canvas, (82, 42, 105), (88, y-12, 330, 55))
                self.text("▶", 102, y-2, self.font, COLORS["accent"])
            self.text(item, 146, y, self.font, COLORS["text"] if not selected else (255,240,255))
        self.text("↑ ↓ / mouse   SPACE / ENTER / click", 88, 760, self.small)

        if self.phobos_body:
            # v6.8: slightly livelier idle without turning him into a bouncing sprite.
            # Slow breathing + tiny weight shift; talking adds only a subtle pulse.
            talking = bool(self.voice_channel and self.voice_channel.get_busy())
            bob = int(3 * math.sin(self.menu_tick / 34.0) + 1.5 * math.sin(self.menu_tick / 79.0))
            sway = int(2 * math.sin(self.menu_tick / 61.0))
            breathe = 1.0 + 0.0025 * math.sin(self.menu_tick / 48.0)
            if talking:
                bob += int(2 * math.sin(self.menu_tick / 5.5))
                sway += int(math.sin(self.menu_tick / 7.0))
            target_h = max(1, int(900 * breathe))
            target_w = int(self.phobos_body.get_width() * target_h / self.phobos_body.get_height())
            body = pygame.transform.scale(self.phobos_body, (target_w, target_h))
            self.canvas.blit(body, (WINDOW_W-target_w+30+sway, 100+bob-(target_h-900)))

        # Facial states are kept as assets for later seamless head-region compositing.
        # v6.6 deliberately does not draw a separate portrait box over Phobos.

    def draw_gameplay_phobos(self):
        if self.phase_index() >= 2 and not self.vtd_active and not self.phobos_route:
            return
        if self.vtd_active and self.vtd_observer:
            source = self.vtd_observer
        elif self.lines >= LINES_PHASE2 and self.phobos_route:
            self.ensure_story100_assets()
            source = self.story100_assets.get("phobos_action") or self.phobos_body
        else:
            source = self.phobos_resistance_body if self.phase_index() == 1 and self.phobos_resistance_body else self.phobos_body
        if not source:
            return
        talking = bool(self.voice_channel and self.voice_channel.get_busy())
        bob = int(2 * math.sin(self.menu_tick / 30.0))
        sway = int(math.sin(self.menu_tick / 52.0))
        if talking:
            bob += int(2 * math.sin(self.menu_tick / 5.0))
        target_h = 390 if self.vtd_active else (390 if self.lines >= LINES_PHASE2 and self.phobos_route else 330)
        target_w = int(source.get_width() * target_h / source.get_height())
        body = pygame.transform.scale(source, (target_w, target_h))
        if self.vtd_active:
            # VTD keeps the green interface, but never draws a green rectangle around the observer.
            x = WINDOW_W - target_w + 30 + sway
            y = WINDOW_H - target_h + 18 + bob
            self.canvas.blit(body, (x, y))
        else:
            x = WINDOW_W - target_w + 35 + sway
            y = WINDOW_H - target_h + 20 + bob
            self.canvas.blit(body, (x, y))

    def draw_records(self):
        self.draw_background("menu")
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        self.canvas.blit(overlay,(0,0))
        title = self.big.render("RECORDS", True, COLORS["accent"])
        self.canvas.blit(title, title.get_rect(center=(WINDOW_W//2, 120)))
        records = self.read_records()
        if not records:
            msg = self.font.render("NO RECORDS YET", True, COLORS["text"])
            self.canvas.blit(msg, msg.get_rect(center=(WINDOW_W//2, 300)))
        else:
            for i, rec in enumerate(records[:10], 1):
                line = f"{i:02d}.   LINES {rec.get('lines',0):3d}     SCORE {rec.get('score',0):6d}"
                surf = self.font.render(line, True, COLORS["text"])
                self.canvas.blit(surf, (205, 190 + (i-1)*62))
        back = self.small.render("SPACE / ENTER / ESC — BACK", True, COLORS["text"])
        self.canvas.blit(back, back.get_rect(center=(WINDOW_W//2, WINDOW_H-70)))

    def draw(self):
        if self.meta_video_name:
            self.draw_meta_video()
        elif self.mode == "intro":
            self.draw_intro()
        elif self.mode == "splash":
            self.draw_splash()
        elif self.mode == "menu":
            self.draw_menu()
        elif self.mode == "records":
            self.draw_records()
        elif self.mode == "settings":
            self.draw_settings()
        elif self.mode == "collection":
            self.draw_collection()
        elif self.mode == "minigame":
            self.draw_minigame()
        else:
            if self.vtd_active:
                self.canvas.fill((0, 0, 0))
            else:
                self.draw_background(self.gameplay_background_phase())
            self.draw_board()
            self.draw_hud()
            self.draw_gameplay_phobos()
            if self.paused:
                self.draw_pause()
            if self.story_overlay is not None:
                self.draw_story_overlay()
            if self.empty_roster_bored and not self.game_over:
                box=pygame.Surface((700,170),pygame.SRCALPHA); box.fill((4,2,8,225)); pygame.draw.rect(box,(110,55,135),box.get_rect(),3)
                self.canvas.blit(box,(90,760))
                self.text("ФОБОС",125,785,self.small,(220,120,245))
                msg=self.font.render("Мне скучно.",True,COLORS["text"]); self.canvas.blit(msg,msg.get_rect(center=(WINDOW_W//2,855)))
            if self.game_over:
                self.draw_game_over()
            if self.phobos_deleted_win:
                ov=pygame.Surface((WINDOW_W,WINDOW_H),pygame.SRCALPHA); ov.fill((0,0,0,225)); self.canvas.blit(ov,(0,0))
                t=self.big.render("ВЫ ВЫИГРАЛИ",True,COLORS["accent"]); self.canvas.blit(t,t.get_rect(center=(WINDOW_W//2,450)))
                st=self.font.render("ФОБОС УДАЛЁН",True,COLORS["text"]); self.canvas.blit(st,st.get_rect(center=(WINDOW_W//2,530)))
                h=self.small.render("НАЖМИТЕ ЛЮБУЮ КЛАВИШУ",True,COLORS["text"]); self.canvas.blit(h,h.get_rect(center=(WINDOW_W//2,620)))
            # Secret effects are top-most, but only during unobstructed Tetris.
            self.draw_secret_effects()

        target_w, target_h = self.window.get_size()
        # Preserve aspect ratio; empty space becomes black letterboxing instead of stretching the board.
        scale = min(target_w / WINDOW_W, target_h / WINDOW_H)
        scaled_w = max(1, int(WINDOW_W * scale))
        scaled_h = max(1, int(WINDOW_H * scale))
        frame = pygame.transform.scale(self.canvas, (scaled_w, scaled_h))
        self.window.fill(COLORS["bg"])
        self.window.blit(frame, ((target_w - scaled_w) // 2, (target_h - scaled_h) // 2))
        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    # Preserve a useful minimum while allowing the player to resize freely.
                    w = max(640, event.w)
                    h = max(520, event.h)
                    self.window = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_click(event.pos, event.button)
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(
                        event.key,
                        getattr(event, "unicode", ""),
                        getattr(event, "mod", 0),
                        getattr(event, "scancode", None),
                    )
                elif event.type == pygame.KEYUP:
                    sc = getattr(event, "scancode", None)
                    if sc is not None:
                        self.held_scancodes.discard(sc)
                elif hasattr(pygame, "WINDOWFOCUSLOST") and event.type == pygame.WINDOWFOCUSLOST:
                    self.held_scancodes.clear()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        self.music.stop()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
