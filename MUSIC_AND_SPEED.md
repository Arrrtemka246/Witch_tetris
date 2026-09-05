# Music and speed setup

## Dynamic music folders

The code contains **no track names**. Put any supported files into:

- `assets/audio/music/phase_0_99_phobos/`
- `assets/audio/music/phase_100_199_resistance/`
- `assets/audio/music/phase_200_plus_guardians/`

Supported: `.mp3`, `.wav`, `.m4a`, `.aiff`, `.aif`.

The game scans the active folder automatically and uses macOS `afplay`, so no extra Python audio package is required. You can add, delete, rename, or replace music without touching `main.py`. The folder is rescanned between tracks, so changes can even be picked up during a running game once the current track ends.

Selection uses a shuffled bag and tries to avoid an immediate repeat across cycles.

## Automatic fall speed

- 0–24 lines: 32 frames
- 25–49: 28
- 50–74: 24
- 75–99: 20
- 100–124: 17
- 125–149: 14
- 150–174: 11
- 175–199: 9
- 200–249: 8
- then 1 frame faster per 50 lines, minimum 3 frames.

Soft drop remains 3 frames or faster if the automatic speed has already reached that level.
