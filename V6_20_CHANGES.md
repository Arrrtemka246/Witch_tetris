# v6.20 — meta-choice routing + horror/vanilla sets

- Secret codes on the 200-line `КТО ПОБЕДИТ?` screen are now context-sensitive endings, not the normal gameplay cheats:
  - VTD / ВТД / ВАЛЕНТИН: continues the current run in locked VTD mode until the run ends.
  - MATRIX / МАТРИЦА: plays the supplied `matrix_intro.mp4` as an in-game prepared frame/audio sequence, then returns to the main menu.
  - JETIX / ДЖЕТИКС: full-screen thank-you screen; SPACE returns to `КТО ПОБЕДИТ?`.
  - PORN / ПОРН: plays the supplied short intro, then asks Y/N before opening one random user-provided external URL; N/ESC returns to the winner choice.
- The same codes outside the winner-choice screen retain their older gameplay/menu behavior.
- Phobos 80% route now uses an actual seven-piece horror sprite bank (I/O/T/J/L/S/Z), with 28 exact rotation assets and strict four-cell tetromino masks.
- Phobos 20% route now uses true sprite-free classic colored tetrominoes, including board, current piece, NEXT and HOLD.
- Vanilla blocks use saturated cyan/blue/orange/yellow/green/purple/red beveled styling based on the supplied reference image.
- Guardians route keeps the light 200+ background; Phobos route keeps the darker 100+ background.
- Phobos route 200+ now uses the casting/action Phobos pose instead of the defeated/resistance pose; the 300-line room uses the casting pose as well.
- The split animation before the 20% vanilla Phobos branch remains in place.
- Matrix source kept in `assets/secrets/videos/matrix_intro.mp4`; prepared playback assets are bundled so pygame does not need a video codec at runtime.
