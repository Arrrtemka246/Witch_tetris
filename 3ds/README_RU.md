# W.I.T.C.H. Tetris — Nintendo 3DS port

Это нативный homebrew-порт проекта на Nintendo 3DS. Он **не запускает Python/Pygame** на консоли: игровой цикл переписан на C++11 с использованием **libctru + Citro2D**.

## Что уже перенесено

Текущий Phase 1 — полноценный игровой vertical slice:

- поле 10×20;
- все 7 тетромино с геометрией из `main.py`;
- вращение по той же схеме и wall-kicks `0, -1, +1, -2, +2`;
- ghost piece;
- soft drop и hard drop;
- HOLD один раз на фигуру;
- NEXT;
- очистка линий;
- очки за 1/2/3/4 линии: 100/300/500/800;
- `+2` очка за клетку hard drop;
- адаптированный Phobos controlled-chaos randomizer из основной версии;
- пауза и Game Over;
- верхний экран — поле/HUD, нижний — управление.

Пока **не перенесены** сюжетные сцены, спрайты персонажей, музыка/озвучка, Collection, секреты и 15 мини-игр. Они будут подключаться поверх уже работающего нативного ядра через RomFS.

## Управление

- D-Pad Left/Right — движение.
- D-Pad Down — soft drop.
- D-Pad Up или Y — hard drop.
- A — вращение по часовой.
- B — вращение против часовой.
- X — HOLD.
- SELECT — пауза.
- START — выход в Homebrew Menu.
- На Game Over: A — начать заново.

## Сборка

Нужны devkitPro/devkitARM и группа пакетов `3ds-dev` (libctru, citro3d, citro2d и инструменты упаковки).

Из корня репозитория:

```bash
make -C 3ds -j2
```

Результат:

- `3ds/witch_tetris_3ds.3dsx`
- `3ds/witch_tetris_3ds.smdh`

### Сборка через Docker

Если devkitPro не установлен локально:

```bash
docker run --rm \
  -v "$PWD:/project" \
  -w /project/3ds \
  devkitpro/devkitarm:latest \
  bash -lc 'dkp-pacman -S --needed --noconfirm 3ds-dev && make -j2'
```

## Установка на 3DS

Скопируйте:

```text
witch_tetris_3ds.3dsx
witch_tetris_3ds.smdh
```

в каталог на SD-карте, например:

```text
/3ds/witch_tetris_3ds/
```

и запускайте через Homebrew Launcher.

## Следующие этапы порта

1. RomFS и конвертация существующих PNG в atlas/t3x, с ограничением памяти Old 3DS.
2. Главное меню, SETTINGS/RECORDS и сохранения на SD.
3. Сюжетные checkpoint-сцены 100/200/300 линий и Phobos room.
4. Аудио через ndsp: заранее подготовленные консольные форматы вместо runtime MP3-декодирования.
5. Character tetromino sprites, horror/Lurden наборы и эффекты очистки.
6. Collection, секретные маршруты и мини-игры.
7. Оптимизация и тестирование на Old 3DS / New 3DS.

Исходная Pygame-версия не изменяется и остаётся основной reference-реализацией для поведения механик.
