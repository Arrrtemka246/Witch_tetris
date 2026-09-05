# v6.35

- Fixed the 200-line route crash: sprite-free tetromino rendering now uses `PLAIN_TETRIS_COLORS`.
- Music state hardened: phase changes clear stale pause state; shuffled track bags are preserved until exhausted.
- Blunk Washing false-water-hit fix: collision now uses a much tighter visible-body zone; drops below Blunk cannot damage him.
- Minigame arena re-centered to a consistent safe playfield instead of clipping oversized mechanics at the window edge.
- Minigames now prefer supplied character faces/action art for Will, Caleb, Taranee, Cornelia, Irma, Blunk and Hay Lin.
- Will Maze now uses the four newly supplied enemy faces and Will's face; Hearts of Kandrakar are used for power items when available.
- Hay Lin Flight uses the existing dark Meridian/Phobos gameplay background. Tower/fence idea intentionally deferred.
- Collection: removed the TRANSFORMATIONS menu item from ART & SPRITES (files retained for cutscene compatibility).
- Phobos room: replaced the old table foreground with the supplied dark rose podium/tribune and removed its white background.
- Phobos room pose sheets were cleaned by removing border-connected white backgrounds/fringe.
- Exact project tetromino geometry remains unchanged.

Note: the supplied PythonPacman repository was used as the design target for the Will Maze conversion. This build switches the presentation to the supplied W.I.T.C.H. faces and retains the integrated in-project maze runtime so the whole game remains one `main.py` application. Further Pac-Man behavior tuning can continue from test feedback.
