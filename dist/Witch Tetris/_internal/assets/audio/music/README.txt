MUSIC FOLDERS — NO FIXED FILE NAMES

Put ANY supported audio files into the phase folder you want.
The game does not care about file names or numbering.

1) phase_0_99_phobos/
   Music for lines 0–99 (Phobos controls the game).
   Example contents: vocal versions, instrumentals, stems/mixes, etc.

2) phase_100_199_resistance/
   Music for lines 100–199 (the spell destabilizes / resistance begins).

3) phase_200_plus_guardians/
   Music for lines 200+ (Guardians vs Phobos's army).

Supported extensions: .mp3, .wav, .m4a, .aiff, .aif

HOW IT WORKS
- Every supported file in the active folder is discovered automatically.
- Names do not matter.
- Add, delete, rename, or replace tracks without changing main.py.
- The folder is rescanned between tracks, including while the game is running.
- Tracks are shuffled and immediate repeats are avoided when possible.
- Non-audio files and macOS .DS_Store are ignored.
- At 100 and 200 lines the current phase playlist stops; the next folder starts after its cutscene.
