# Character sprite system v5

Phase I mapping is fixed:
- I = Cornelia
- T = Caleb
- O = Blunk
- L = Hay Lin
- J = Taranee
- S = Irma
- Z = Will

Changes in v5:
- Cell size increased from 16 px to 24 px.
- Character artwork is rotated as one complete image by 90/180/270 degrees before it is split into cells.
- The game geometry uses the exact same rotation transform as the artwork, so the image and collision cells stay synchronized.
- When a piece locks, each cell keeps its exact fragment. Line clearing can therefore leave individual body/image fragments on the board intentionally.
- Caleb now uses the newer clean T artwork supplied by the user.
- Taranee/J uses the newer G/J block supplied by the user.

Generated atlases:
- assets/sprites/phase1/phase1_atlas_bank1.png
- assets/sprites/phase1/phase1_atlas_bank2.png
- assets/sprites/phase1/phase1_atlas.json

Debug/verification image:
- assets/sprites/phase1/rotation_preview_v5.png

Each source image can later be replaced, but the replacement should preserve the same tetromino grid geometry.
