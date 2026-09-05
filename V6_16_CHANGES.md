# v6.16

- Blunk line-clear voice reactions are substantially more frequent: 68% on a 1-line clear and 82% on a 2-line clear. `fight.wav` joins the 1-line pool.
- Gameplay Phobos now has a dedicated resistance sprite for 100–199 lines (`assets/menu/phobos/resistance_body.png`). It switches automatically at 100 lines and disappears at 200+ as before.
- Rebuilt Intro Phobos transparency from the original source art. Dark robe areas are preserved instead of being treated as black background.
- Intro typewriter is slightly faster: 3 frames/character instead of 4.
- Intro dialogue now auto-continues after the text has been readable for a short time. SPACE still completes/advances, A/F still skips the current beat, ESC skips Intro.
- Added `INTRO` to the main menu so the opening cutscene can be replayed at any time. Each replay rerolls the random speaker, transformation branch, and final Phobos line.
- HUD order changed to the conventional layout: NEXT on top, HOLD below it.
- Added `VOICE_USAGE_V6_16.md`: complete voice-file registry showing which files are currently wired into gameplay and which are still unused.
