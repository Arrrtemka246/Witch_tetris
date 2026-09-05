# Установка Pygame-версии на macOS

## Вариант A — рекомендованный: отдельное окружение проекта

Открой Terminal и перейди в папку игры:

```bash
cd ~/Documents/Games/Witch_tetris
```

Создай виртуальное окружение:

```bash
python3 -m venv .venv
```

Активируй его:

```bash
source .venv/bin/activate
```

Обнови pip:

```bash
python -m pip install --upgrade pip
```

Установи зависимости проекта:

```bash
python -m pip install -r requirements.txt
```

Запуск:

```bash
python main.py
```

При следующем запуске достаточно:

```bash
cd ~/Documents/Games/Witch_tetris
source .venv/bin/activate
python main.py
```

## VS Code

1. Открой папку `Witch_tetris` в VS Code.
2. Нажми `Cmd + Shift + P`.
3. Выбери `Python: Select Interpreter`.
4. Выбери `.venv/bin/python`.
5. После этого `main.py` можно запускать кнопкой Run.

## Проверка Pygame

```bash
python -c "import pygame; print(pygame.version.ver)"
```

## Если команда python3 указывает не туда

Проверь:

```bash
which python3
python3 --version
```

На Apple Silicon Homebrew-Python обычно расположен в `/opt/homebrew/bin/python3`.
