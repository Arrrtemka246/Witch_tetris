# W.I.T.C.H. Tetris v6.17 — 100-line cutscene / fourth-wall crash

## Scene 2: 100 lines
- Replaced the old static 100-line overlay with a multi-stage cutscene.
- Start: gameplay picture glitches, audio stutters/crashes, then cuts to black.
- Fake in-game terminal boot (`MERIDIAN CONTROL SYSTEM / PHOBOS SPELL ENGINE v1.0`).
- Terminal checks all seven bindings, reports 49% integrity, recovery failure, and loss of control.
- Four random fourth-wall jokes are chosen per run from a larger pool.
- `PRESS ANY KEY` really accepts any keyboard key; left mouse click also continues.
- Immediately after input, terminal answers `ERROR: PLAYER PRESSED A KEY`, glitches out, then reveals the spell failure in the throne hall.
- Guardians flicker between normal and tetromino forms; Will/other random speaker reacts; Phobos struggles and switches to his weakened 100–199 sprite.
- Final card: `ЗАКЛИНАНИЕ СЛАБЕЕТ / СОПРОТИВЛЯЙТЕСЬ`, Space returns to gameplay.

## Exact terminal variant probabilities
- 50% — plain text terminal, no large silhouette.
- 12.5% — Heart of Kandrakar text silhouette.
- 12.5% — Jetix mascot text silhouette.
- 12.5% — ordinary heart text silhouette.
- 12.5% — large Q text silhouette.

Heart of Kandrakar and Jetix masks are derived from the supplied reference images. They are not black fills: the shapes are built from terminal words such as ERROR, FAILED, PHOBOS, WILL, IRMA, MERIDIAN, KANDRAKAR, PLAYER, 49%, etc.

## Other fixes included
- 100–199 Phobos portrait replaced with the newly supplied hunched/weakened sprite.
- Intro Will/Irma intermediate transformation stage assets swapped back to their correct character chains.
- Intro Phobos normal/cast alpha rebuilt conservatively and the lower cloak made intentionally solid/opaque to prevent the recurring transparent-cloak problem.
- Intro final Phobos pool expanded and weights made less dominated by the same two lines.
- 200+ now marks a session victory; the temporary checkpoint card says YOU WIN / PHOBOS DEFEATED / FREE PLAY UNLOCKED until the full 200-line cinematic is built.
- After a victory, `you_loser` is disabled for the rest of the app session. Free Play run endings do not trigger Phobos defeat taunts.
