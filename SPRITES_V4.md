# Character sprite prototype v4

This build integrates the seven current Phase-I character tetromino images.

- I — Cornelia
- T — Caleb
- O — Blunk
- L — Hay Lin
- J — Taranee
- S — Irma
- Z — Will

## Behaviour
The active piece uses four image fragments. Rotation changes both Tetris geometry and image orientation. When the piece locks, every cell keeps its own fragment. Normal line clearing can therefore leave isolated visual fragments; this is deliberate.

Phase II still uses fallback army blocks until army artwork is added.
