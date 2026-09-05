# v6.19 META ROUTES — fixes after v6.18

- Secret-code input is now fed before menu/story handlers, so codes work in the main menu and on the 200-line winner-choice screen.
- Secret overlays/effects render above menu and story overlays; their timers also tick while in the menu.
- VTD entered in the menu is carried into a subsequently started game.
- The 200-line `КТО ПОБЕДИТ?` buttons are centered inside the 860px internal canvas; neither option extends outside the game window.
- Guardians route after 200 keeps the light/liberated 200+ background.
- Phobos route after 200 keeps the dark 100–199 Resistance background and uses the weakened/resistance Phobos body.
- Phobos 20% `ordinary pieces` route now means true vanilla tetrominoes: no character artwork on current/NEXT/HOLD/locked cells. Existing locked cells are converted too.
- Before that vanilla Phobos branch starts, a 3-second splitting animation removes the Guardian character imagery.
- The 300-line Phobos route is now a real fake-crash sequence: glitch -> blackout -> room with Phobos. Gameplay is fully suspended there; Phobos speaks from a non-repeating pool after a short silence and about every 40 seconds afterwards. ESC safely returns to the main menu.
- Guardians victory now also blocks Phobos files passed through the external/queued voice helpers, closing a path that could let old Phobos lines leak after 200.
- User-provided Matrix/Pornhub MP4 source files and the current seven horror-character source images are bundled under assets for the next media/sprite pass.
