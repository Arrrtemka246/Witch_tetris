# v6.32 — Arcade pass

- All Collection mini-games now have an explicit GAME OVER state.
- Space/Enter retries; Esc/X returns to Collection; mouse buttons work on the Game Over overlay.
- Mini-games are endless arcade loops: cleared waves respawn harder rather than ending in victory.
- Will Maze rebuilt around a collision maze, pellets, four power Hearts, lives, frightened enemies, wave reset, and four different target behaviours.
- Heart Breaker: harder rebounds, shrinking paddle, speed growth, lives, endless brick waves.
- Taranee Fire Shot: enemy fire, descending formation, faster waves, lives and overrun Game Over.
- Hay Lin / Caleb / Snake now end on collision instead of silently resetting or subtracting score.
- Cornelia uses a corruption meter; Blunk, Bubble Trouble, Rain Dance and Whirlpool now have loss conditions.
- Irma Whirlpool simplified: gold debris must be PULLED IN, red enemies REPELLED OUT; Space toggles mode.
- Gallery previews are fitted and clipped to the preview pane.
- Mini-game rendering is clipped to the arena so objects cannot spill outside the game window.
- Existing test-build rule remains: Collection and mini-games are unlocked.
