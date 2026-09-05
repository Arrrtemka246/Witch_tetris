# W.I.T.C.H. Tetris — v6.5

- Restored startup flow: splash -> main menu -> NEW GAME / RECORDS / QUIT.
- Added temporary 16-bit palace splash/menu background.
- Added three distinct gameplay backgrounds for 0-99, 100-199, and 200+ lines.
- Added Phobos menu art plus a simple idle facial portrait animation using the supplied expression sheet.
- Matrix, Jetix, porn and VTD English physical-key codes now work independently of the active EN/RU keyboard layout.
- Russian textual aliases still work independently through Unicode input.
- WASD/W/X/Z/C and developer/music controls use physical scancodes so switching macOS layout cannot break gameplay.
- Jetix cameo rebuilt: appears in the corner, bounces, squashes/winks, somersaults, exits, with colored confetti.
- 200+ sprite loader now checks assets/sprites/phase2/lurdens for replacement I/T/O/L/J/S/Z art and falls back safely to phase1 until those assets are ready.
- Records screen restored; top 10 runs are saved to records.json.
- Existing Hold, pause, secrets, music phases, story checkpoints, transparency and auto-fit rendering are preserved.

Temporary note: the current splash and backgrounds are placeholder 16-bit assets and can later be replaced by the final intro/video/frame sequence without changing game logic.
