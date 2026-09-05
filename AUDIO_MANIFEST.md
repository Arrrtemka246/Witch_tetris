# Аудио-аудит актуальной v6.37.1

Таблица составлена по реальным вызовам в `main.py`. Вероятность указана для соответствующего события, а не для всей игровой сессии. Озвучка может не сработать, если в этот момент уже звучит другая реплика или действует общий 18-секундный cooldown.

## Музыка

| Файл или группа | Используется | Где | Вероятность / порядок |
|---|---:|---|---|
| `music/menu/menu_1.mp3` | Да | Главное меню, также доступен в Collection | Перемешиваемая очередь из двух треков: первый выбор 50%, каждый звучит один раз за цикл |
| `music/menu/menu_2.mp3` | Да | Главное меню, также доступен в Collection | Перемешиваемая очередь из двух треков: первый выбор 50%, каждый звучит один раз за цикл |
| `collection/intro_music.mp3` | Да | Всё интро | 100%; теперь продолжает играть между сценами без перезапуска |
| `music/phase_0_99_phobos/Arrogant_Prince_of_the_Obsidian_Court.mp3` | Да | Основной Tetris, 0–99 линий | Единственный трек этапа: 100% |
| `music/phase_100_199_resistance/phase2_1.mp3` | Да | Основной Tetris, 100–199 линий | Перемешиваемый мешок из трёх: первый выбор 33,3%, каждый трек звучит раз за цикл |
| `music/phase_100_199_resistance/phase2_2.mp3` | Да | Основной Tetris, 100–199 линий | То же: 33,3% первым, гарантирован раз за цикл |
| `music/phase_100_199_resistance/phase2_3.mp3` | Да | Основной Tetris, 100–199 линий | То же: 33,3% первым, гарантирован раз за цикл |
| `collection/phase2_1.mp3` | Да | Ручное прослушивание в Collection | Только при выборе; побайтная копия сюжетного `phase2_1.mp3` |
| `collection/phase2_2.mp3` | Да | Ручное прослушивание в Collection | Только при выборе; побайтная копия сюжетного `phase2_2.mp3` |
| `collection/phase2_3.mp3` | Да | Ручное прослушивание в Collection | Только при выборе; побайтная копия сюжетного `phase2_3.mp3` |
| `collection/witch_ending.mp3` | Да | Ветка победы Стражниц после 200 линий и Collection | 100%, пока папка `phase_200_plus_guardians` пуста |
| `music/phobos_route/Phobos_main_theme_3_phase.mp3` | Да | Ветка победы Фобоса после 200 линий и Collection | Единственный трек этапа: 100% |
| `music/phobos_room/PhobosthemeDark.mp3` | Да | Комната Фобоса и Collection | 100% при входе в комнату, зациклен |
| `collection/minigames_1.mp3` | Да | Collection; запасной трек мини-игр | В игре — только если отсутствуют все `arcade_*.mp3`; сейчас вероятность 0% |
| `collection/minigames_2.mp3` | Да | Collection | Только при ручном выборе |
| `minigames/arcade_1.mp3` … `arcade_6.mp3` | Да | Все мини-игры, кроме Snake и Blunk Washing | Общий мешок: каждый файл один раз за шесть запусков/повторов; вероятность быть первым — 16,7% |
| `minigames/blunk_snake.mp3` | Да | Snake за Бланка | Бланк выбирается случайно в 50% запусков Snake; тогда этот трек звучит всегда |
| `minigames/snake_1.mp3` … `snake_4.mp3` | Да | Snake за Седрика или Фобоса | Седрик/Фобос вместе — 50% запусков; каждый файл имеет 25% внутри пула, то есть 12,5% от случайного старта Snake |
| `minigames/blunk_washing_1.mp3` … `blunk_washing_4.mp3` | Да | Blunk Washing | Равный случайный выбор: 25% на файл при каждом запуске или повторе |
| `music/secrets/vtd/vtd_01.mp3`, `vtd_02.mp3` | Да | Секретный код `VTD`/`ВТД`/`ВАЛЕНТИН` во время основного Tetris | По 50% при запуске; смена музыки выбирает другой файл |
| `minigames/bonus_1.mp3`, `bonus_2.mp3` | Нет | Не назначены | 0% |
| `minigames/crucified.mp3`, `crusified2.mp3` | Нет | Не назначены | 0% |
| `minigames/phobos_empty_hollow_1.mp3`, `phobos_empty_hollow_2.mp3` | Нет | Резерв Empty Hollow | 0% |
| `reserve/football_1.mp3`, `football_2.mp3` | Нет | Резерв будущей игры | 0% |
| `reserve/sobak_1.mp3`, `sobak_2.mp3` | Нет | Резерв будущей игры | 0% |

## Эффекты

| Файл или группа | Используется | Где | Вероятность / правило |
|---|---:|---|---|
| `collection/phobos_type_tick.wav` | Да | Печатание текста в комнате Фобоса | Каждые три кадра во время появления букв |
| `sfx/line_clear_a.wav`, `line_clear_b.wav` | Да | Удаление 1–3 линий в обычной ветке | Случайно, по 50% на эффект |
| `sfx/heart_portal.wav` | Да | Tetris из четырёх линий в обычной ветке | 100% события, если не перекрывается озвучкой Вилл |
| `sfx/phobos_laughs/laugh_1.wav` … `laugh_3.wav` | Да | Tetris из четырёх линий в ветке Фобоса | Равный выбор: 33,3% на файл |
| `sfx/intro/lightning.wav`, `ominous_hit.wav`, `transform_drone.wav`, `text_blip.wav`, `new_magic_1.wav`, `new_magic_2.wav` | Да | Заданные моменты интро и печатание неозвученного текста | Не случайные; зависят от сцены |
| `sfx/Laught(1).m4a`, `Laught2(1).m4a`, `Laught3(1).m4a` | Нет | Исходные M4A, заменены WAV-копиями в `phobos_laughs` | 0% |
| `sfx/Long_sfx(1).m4a`, `SFX(1).m4a`, `Sfx_(1).m4a`, `Sfx_short(1).m4a` | Нет | Не назначены | 0% |
| `sfx/new_sfx_a.wav`, `new_sfx_b.wav` | Нет | Не назначены | 0% |

## Озвучка — основные и редкие события

| Файл или группа | Используется | Где | Вероятность / правило |
|---|---:|---|---|
| `phobos/meridian_mine.mp3`, `dark_side.mp3`, `extra/lets_begin.wav`, `extra2/your_power_is_nothing.wav`, `last_hope_universe.wav`, `new_era_phobos.wav` | Да | Начало новой игры | Сначала общий шанс реплики 65%; веса внутри пула: 25%, 25%, 24%, 9%, 8%, 9% |
| `extra2/your_power_is_nothing.wav`, `new_era_phobos.wav`, `dark_side.mp3`, `extra/brilliant_laugh.wav`, `extra/lets_begin.wav`, `meridian_mine.mp3`, `extra2/haha_no_way.wav` | Да | Финал интро | Соответственно 20%, 16%, 16%, 14%, 12%, 10%, 12% |
| `extra2/expected_no_less.wav` | Да | Обычный Game Over до победы | 38%, кроме особой реплики серии поражений |
| `extra2/you_loser.wav` | Да | Серия поражений | Один раз при пятом последовательном Game Over или позже |
| `extra2/failed_last_time.wav` | Нет | Ошибочно был в Game Over | 0%; это 145,2-секундный `Untitled Project 1`, выбор из кода отключён |
| `will/we_are_one.wav`, `one_short.wav`, `we_are_one_2.wav`, `we_are_one_3.wav` | Да | Tetris из четырёх линий при активной Вилл | По 25% на файл |
| `phobos/not_bad.mp3` | Да | Ответ Фобоса после реплики Вилл или отдельная реакция на Tetris | 55% после Вилл; 55% как самостоятельная реакция, если Вилл удалена |
| `guardians/cornelia/earth_1.wav` … `earth_3.wav` | Да | Обычная очистка линий фигурой Корнелии | После 5% шанса перебивки Фобоса; затем равный выбор одного из трёх |
| `guardians/irma/water_1.wav` … `water_3.wav` | Да | Обычная очистка линий фигурой Ирмы | То же |
| `guardians/taranee/fire_1.wav` … `fire_3.wav` | Да | Обычная очистка линий фигурой Тарани | То же |
| `guardians/haylin/air_1.wav` … `air_3.wav` | Да | Обычная очистка линий фигурой Хай Лин | То же |
| `extra2/destroy_weak_link.wav` | Да | Редкая перебивка обычной очистки | 5% подходящей очистки |
| `caleb/im_15.wav` | Да | Обычная очистка фигурой Калеба | 40% после проверки 5% перебивки Фобоса |
| `blunk/businessman.wav`, `laugh.wav`, `groan.wav`, `fight.wav` | Да | Очистка одной линии Бланком | Общий шанс 68%, затем равный выбор одного из четырёх |
| `blunk/also_warrior.wav`, `treasure.wav`, `not_afraid.wav` | Да | Очистка двух линий Бланком | Общий шанс 82%, затем равный выбор одного из трёх |
| `extra/name_traitors.wav`, `phobos/rebel.mp3` | Да | Появление Калеба | 4,5%; если первая не сработала — 2,5% для второй; каждая максимум один раз за игру |
| `phobos/blunk_angry.mp3`, `blunk_annoyed.mp3` | Да | Появление Бланка | Общий шанс 3,5%; выбирается одна ещё не звучавшая реплика |
| `extra2/need_crystal.wav`, `phobos/crystal.mp3`, `extra2/well_girls.wav` | Да | Появление Вилл | Последовательные проверки 4,5%, 4,5% и 1,8%; каждая максимум один раз за игру |
| `extra2/well_girls.wav`, `guardian_of_veil.mp3` | Да | Появление элементальной Стражницы | 1,8%, затем 0,8%; каждая максимум один раз за игру |
| `rotate_hint.mp3` | Да | Чрезмерное вращение одной фигуры | 5-е вращение 12%, 6-е 24%, 7-е 38%, 8-е 55%, 9-е и далее 72%; после срабатывания блок на пять фигур |
| `hold_hint.mp3` | Да | Частое использование Hold | 35% после семи Hold, если голосовой канал свободен |
| `pause_hint.mp3` | Да | Долгая игра без паузы | Проверки начинаются через случайные 150–420 секунд; затем 18% каждые 10 секунд, максимум один раз за игру |
| `layout_wont_help.mp3` | Да | Первая смена RU/EN раскладки во время основного Tetris | 8%, один раз за игру |
| `porn_reaction.mp3` | Да | Английский код `PORN` | 20% после ввода кода |
| `matrix_fan.mp3` | Да | Код `MATRIX` | 2% после ввода кода |
| `extra2/you_will_pay_short.wav`, `you_will_pay_full.wav` | Да | Сцена сопротивления на 100 линиях | Равный выбор: 50% на файл |
| `extra2/rage_roar.wav` и `blunk/groan.wav` | Да | Крики при очистке линий в ветке Фобоса | Равный выбор; при четырёх линиях очередь заменяется смехом Фобоса |

## Озвучка, которая сейчас лежит в проекте, но не вызывается

- `voice/menu/new_game.wav`, `records.wav`, `quit.wav` — озвучка меню отключена по решению автора.
- `voice/pause_menu/continue.wav`, `restart.wav` — озвучка паузы отключена.
- `voice/will/to_battle.wav`.
- `voice/phobos/knights_forward.mp3`, `lines_200_rage.mp3`.
- `voice/phobos/extra/anger.wav`, `brilliant.wav`, `hurry.wav`, `well.wav`.
- `voice/phobos/extra2/cant_end_like_this.wav`, `freedom_laugh.wav`, `ill_decide.wav`, `say_it.wav`, `tears.wav`, `tears_then_what_full.wav`, `what.wav`, `what_do_you_want.wav`, `whats_wrong_full.wav`, `whats_wrong_short.wav`, `why_plan_failed.wav`, `no_need_to_hurry.wav`, `waiting_achieves.wav`.

Последняя группа раньше готовилась для реакций меню паузы и дополнительных событий, но её пул сейчас намеренно не вызывается.
