# v5 changes

1. Fixed character rotation. The complete character grid is rotated first; only then is it split into four game-cell fragments.
2. Increased game cell/sprite resolution from 16x16 to 24x24. Window enlarged to 440x540.
3. Replaced Caleb T source with the latest supplied image.
4. Kept the latest supplied Taranee J/G source.
5. Music process cleanup is now in a `finally` block around `pyxel.run`; closing the game window terminates `afplay`. The stop routine also escalates to `kill()` if termination times out.
6. Dynamic music-folder behavior and progressive speed system from v3/v4 remain intact.
