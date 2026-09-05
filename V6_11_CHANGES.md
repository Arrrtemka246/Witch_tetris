# v6.11 changes

- Character-addressed spawn lines are now once-per-game per concrete line; reset/restart clears the flags.
- Fixed Will/Irma binding: Will is S, Irma is Z. The Heart/Crystal Phobos line now targets S/Will and can fire once per game.
- Rotation hint starts checking on the 5th spin with increasing probability; after it fires, the next five spawned pieces are protected before it can become eligible again.
- Added Guardian elemental line-clear voice pools for 1-3 rows: I/Cornelia=Earth, Z/Irma=Water, J/Taranee=Fire, L/Hay Lin=Air. Alternate performances are randomized; literal duplicate files are not duplicated.
- Tetris uses a pool of distinct Will "we are one" performances, then keeps Phobos "Not bad, not bad" at 55%, queued so dialogue does not overlap.
- Tetris Heart SFX is faded before dialogue; 1-3 line SFX uses the two supplied line-clear alternatives.
- Heart of Kandrakar black border/background is removed at runtime and it remains centered on the four clearing rows with translucent pink row tint.
- Pause menu now has voice-over for CONTINUE / RESTART / MAIN MENU, with hover/selection anti-spam delay.
- VTD / ВТД / ВАЛЕНТИН now activates a full Matrix visual mode: black background, green board/tetromino/HOLD/NEXT treatment, digital green overlay, and the submitted VTD observer replaces Phobos. Leaving VTD with ? or when the VTD track ends restores the normal scene.
- The standalone MATRIX code remains its own interface-only easter egg.
- Added the newly supplied unique dialogue/SFX assets to the project registry for future trigger tuning.
- Start voice pool now also includes "Начнём" alongside the two existing Phobos intros.
