# v6.18 META branch

- Kept the complete v6.17 100-line fake-crash / terminal cutscene.
- Scene 2: X skips the whole cutscene; SPACE/ENTER advances the current beat.
- Terminal random variant remains: 50% plain text; 12.5% Kandrakar Heart; 12.5% Jetix; 12.5% ordinary heart; 12.5% Q.
- Will is less likely to be the resistance speaker.
- Phobos scene-2 threat now uses the supplied `you_will_pay_short/full` recordings when present.
- At 200 lines the game asks WHO WINS: GUARDIANS or PHOBOS.
- Guardians route: Phobos voice/pause reactions are disabled for the rest of that run/session; free play continues with the normal exact tetromino set.
- Phobos route: laugh + 80% horror-mode flag / 20% ordinary-mode flag; at 300 lines the game enters a Phobos room and he speaks a random available line roughly every 40 seconds.
- Lurden replacement set is intentionally not used; phase 200+ falls back to the normal tetromino art.
- VTD observer no longer has the unwanted green rectangle around the character (the Matrix-style UI tint remains).
- Exact gameplay geometry remains I/O/T/S/Z/J/L from BASE_SHAPES; art never changes collision geometry.

Still asset-dependent / not final:
- Full animated 200-line reverse-transformation and Phobos disintegration sequence.
- Final horror sprites for all seven tetrominoes in all required rotations.
- Matrix MP4 ending (video file not supplied yet).
- Jetix thank-you card artwork/animation for the 200-line choice branch.
- More Guardian/Blunk voice recordings for post-Phobos pause/menu reactions.
