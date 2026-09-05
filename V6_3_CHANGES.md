# W.I.T.C.H. Tetris — Pygame v6.3

## Controls
- Left/Right or A/D — move
- Down or S — soft drop
- Up — hard drop
- Z/X/W — rotate
- C / Left Shift / Right Shift — HOLD
- Space — pause / continue
- Esc — pause
- F11, Cmd+Enter, Alt+Enter — fullscreen
- M — music
- Shift+Q — developer cheat: +10 lines

## Story checkpoints
- 100 lines — resistance checkpoint overlay
- 200 lines — break-free checkpoint overlay / endless phase begins
- Game Over now has its own screen instead of silently restarting.

## Secret codes
Codes use the actual typed characters (`event.unicode`), so Russian and English layouts can trigger different secrets.
- `porn` — pauses gameplay and opens one random image from `assets/secrets/porn/`; Space returns to the exact game.
- `порн` — large `18+` overlay for about one second.
- `vtd`, `втд`, `валентин` — randomly plays one of the tracks in `assets/audio/music/secrets/vtd/`; normal phase music resumes afterwards.
- `matrix`, `матрица` — temporary green Matrix-style interface effect; tetromino character sprites are not recolored.
- `jetix`, `джетикс` — temporary celebratory Jetix overlay using `assets/secrets/jetix/Jetix.png`.

Secret image folders are scanned dynamically. New images/tracks can be added without hard-coding filenames.
