# v6.12 changes

Gameplay/voice fixes requested after v6.11:

- Corrected the project’s real sprite mapping: **S = Irma**, **Z = Will**.
  - Water reactions now belong to S/Irma.
  - Z/Will has no invented elemental line on ordinary 1–3 row clears.
  - Will-specific Phobos reactions now trigger from Z/Will spawns.
- Will spawn reactions can use “Мне нужен кристалл” and the older Heart/Crystal line, each at most once per game.
- “Ну надо же, девочки” can rarely react to a Guardian spawn, at most once per game.
- Caleb/T: “Детка, мне уже 15” moved from spawn chatter to line-clear gameplay reaction.
- Blunk/O line-clear logic now respects O-piece geometry:
  - one-row clears use a lighter Blunk pool;
  - two-row clears use stronger Blunk reactions;
  - no Blunk 3-row or 4-row reaction can be selected.
- Normal 1–3 row clears have a small (~5%) chance for Phobos to replace the character reaction with “Уничтожь слабое звено…”.
- Pause opening no longer automatically says “Продолжить”. Pause menu labels are voiced only after the player actually changes/points at an item.
- Added a rare pause-reaction pool (“Ну что там?”, waiting/what’s-wrong style lines) and a rare “Пусть так. Поспеши” reaction on resume.
- Rotation hint now bypasses only the long global voice cooldown when the voice channel is idle. It still never interrupts active dialogue and still keeps the five-piece anti-repeat block.
- Expanded low-probability start-game Phobos pool with “Теперь ваша сила против моей — ничто”, “последняя надежда вселенной”, and “новая эра Фобоса”.
- Added Game Over reactions. “Ну ты и лох” is reserved for the fifth consecutive Game Over in the same app session, once per session.
- “Сейчас ты заплатишь…” remains unused for now.
- “Нет! Так не может кончиться…” remains reserved for a future final cutscene.

Existing VTD/Matrix, Heart of Kandrakar, Tetris Will sequence, 55% “Неплохо, неплохо”, music folders and secret-code behavior are preserved.
