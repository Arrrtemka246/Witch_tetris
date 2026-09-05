# Pygame v6.1 changes

- Internal character cell resolution remains 50x50 pixels.
- The window now auto-fits the physical display instead of opening taller than the screen.
- The final 50px-cell frame is scaled with nearest-neighbour scaling and keeps its aspect ratio.
- F11 toggles fullscreen.
- The window can be resized; black letterboxing prevents stretching/distortion.
- Near-black background pixels connected to sprite image edges are converted to transparent alpha at load time.
- Black outlines/details inside the character are preserved where possible.
- Sprite scaling uses nearest-neighbour rather than smooth scaling to keep the pixel/SNES look crisp.
- Hold, pause, dynamic music folders, speed progression and the previous rotation system are preserved.
