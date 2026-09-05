# WITHC TETRIS — ASSET CHECKLIST

Keep every project file under one root folder, for example:
`~/Documents/games/withc_tetris/`

Source PNG/WAV files live under `assets/`. Runtime Pyxel resources live under `resources/`.

## Graphics

| File | Size | Purpose | Folder |
|---|---:|---|---|
| menu_background.png | 320x360 | Main menu background | assets/images/backgrounds |
| gameplay_background.png | 320x360 | Phase 1 gameplay background | assets/images/backgrounds |
| phase2_background.png | 320x360 | Phase 2 gameplay background after 200 lines | assets/images/backgrounds |
| records_background.png | 320x360 | Records screen background | assets/images/backgrounds |
| intro_cutscene.png | 320x360 | Intro cutscene | assets/images/cutscenes |
| victory_100_cutscene.png | 320x360 | Cutscene at 100 lines | assets/images/cutscenes |
| game_over_cutscene.png | 320x360 | Bad/game-over cutscene | assets/images/cutscenes |
| transformation_200_cutscene.png | 320x360 | Transition into Phase 2 at 200 lines | assets/images/cutscenes |
| tetromino_i.png | 16x16 | I character/block sprite | assets/sprites/base |
| tetromino_o.png | 16x16 | O character/block sprite | assets/sprites/base |
| tetromino_t.png | 16x16 | T character/block sprite | assets/sprites/base |
| tetromino_s.png | 16x16 | S character/block sprite | assets/sprites/base |
| tetromino_z.png | 16x16 | Z character/block sprite | assets/sprites/base |
| tetromino_j.png | 16x16 | J character/block sprite | assets/sprites/base |
| tetromino_l.png | 16x16 | L character/block sprite | assets/sprites/base |
| tetromino_i_phase2.png | 16x16 | Phase 2 I sprite | assets/sprites/phase2 |
| tetromino_o_phase2.png | 16x16 | Phase 2 O sprite | assets/sprites/phase2 |
| tetromino_t_phase2.png | 16x16 | Phase 2 T sprite | assets/sprites/phase2 |
| tetromino_s_phase2.png | 16x16 | Phase 2 S sprite | assets/sprites/phase2 |
| tetromino_z_phase2.png | 16x16 | Phase 2 Z sprite | assets/sprites/phase2 |
| tetromino_j_phase2.png | 16x16 | Phase 2 J sprite | assets/sprites/phase2 |
| tetromino_l_phase2.png | 16x16 | Phase 2 L sprite | assets/sprites/phase2 |
| game_logo.png | <=240x64 | Optional logo | assets/images/ui |
| menu_cursor.png | 16x16 | Optional menu cursor | assets/images/ui |
| board_frame.png | about 168x328 | Optional Phase 1 board frame | assets/images/ui |
| hud_panel.png | about 120x320 | Optional Phase 1 HUD | assets/images/ui |
| phase2_board_frame.png | about 168x328 | Optional Phase 2 board frame | assets/images/ui |
| phase2_hud_panel.png | about 120x320 | Optional Phase 2 HUD | assets/images/ui |
| game_over_emblem.png | <=128x128 | Optional game-over emblem | assets/images/ui |
| record_crown.png | 16x16 or 24x24 | Optional records icon | assets/images/ui |
| icon_lines.png | 16x16 | Optional lines icon | assets/images/ui |
| icon_next.png | 16x16 | Optional next-piece icon | assets/images/ui |
| icon_phase1.png | 16x16 | Optional Phase 1 icon | assets/images/ui |
| icon_phase2.png | 16x16 | Optional Phase 2 icon | assets/images/ui |
| icon_pause.png | 16x16 | Optional pause icon | assets/images/ui |

## Audio

| File | Purpose | Folder |
|---|---|---|
| gameplay_music.wav | Phase 1 music | assets/audio/source |
| phase2_music.wav | Different endless Phase 2 music after 200 lines | assets/audio/source |
| rotate.wav | Rotation SFX | assets/audio/source |
| line_clear.wav | Line-clear SFX | assets/audio/source |
| hard_drop.wav | Hard-drop SFX | assets/audio/source |
| menu_select.wav | Menu SFX | assets/audio/source |
| cutscene_transition.wav | Cutscene transition SFX | assets/audio/source |
| game_over.wav | Game-over SFX | assets/audio/source |

## Pyxel runtime resources

- `resources/main_game.pyxres` — Phase 1 sprites, sounds and music.
- `resources/phase2.pyxres` — Phase 2 sprites and the different Phase 2 music.

The current code switches to `phase2.pyxres` and starts `MUSIC_PHASE2` when the 200-line transition is completed.
