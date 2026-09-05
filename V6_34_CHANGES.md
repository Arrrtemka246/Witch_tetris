# v6.34 — crash hotfix + arcade audio + minigame bounds

- Restored `fall_interval()` so NEW GAME no longer crashes with `AttributeError` on the first gameplay update.
- Restored the full opening INTRO on application launch.
- Minigame actors, projectiles, hazards and spawns now use the actual minigame arena bounds instead of spawning beyond the visible play area.
- BLUNK WASHING now draws Blunk instead of a generic paddle. Existing four Blunk Washing music tracks are unchanged.
- Retry/continue restarts the active minigame soundtrack from the beginning.
- Snake random character weights: 50% Blunk, 25% Cedric, 25% Phobos.
- Blunk Snake uses `blunk_snake.mp3`; Cedric/Phobos use the shared Snake pool.
- Cedric Snake now eats the Phobos face; Blunk collects gold; Phobos collects the Heart of Kandrakar.
- Cornelia Earth Garden is harder: faster/more frequent vines, crowding corruption and weaker/narrower cleansing.
- Irma Whirlpool supports held Left/Right aiming.
- Added three more generic arcade tracks (`arcade_3..5`) to the rotating shuffled arcade bag.
- Phobos stage 3 now contains two interchangeable tracks: `Phobos_theme_1.mp3` and `Phobos_main_theme_3_phase.mp3`. MusicPool shuffles them like the other route pools.
- `PhobosthemeDark.mp3` remains exclusive to the Phobos room.
- `football_1/2` and `sobak_1/2` are packaged under `assets/audio/reserve/` for future use and are not played yet.
- The forbidden voice line “Заклинание Фобоса рушится” remains absent from packaged audio and blocked in code.
