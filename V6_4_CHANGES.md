# v6.4 — keyboard-layout / secret-code input fix

- Fixed a bug where secret-code prefix detection could swallow gameplay letters and make WASD-style controls appear to stop working.
- Secret codes now use a rolling text buffer and never consume movement/rotation/HOLD input.
- `matrix` and `матрица` are both detected by suffix matching, which is tolerant of an accidental extra character/repeat before the code.
- WASD-family gameplay controls now use physical SDL scancodes, so they work regardless of English/Russian macOS keyboard layout.
- Physical controls:
  - A / D positions: move left/right
  - S position: soft drop
  - W / X / Z positions: rotate
  - C / left Shift / right Shift positions: HOLD
  - Up arrow: hard drop
  - Space: pause/resume
- Held physical S is tracked with KEYDOWN/KEYUP and cleared if the window loses focus.
