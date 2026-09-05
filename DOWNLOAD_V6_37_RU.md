# Как скачать W.I.T.C.H. Tetris v6.37.0

## Самый простой способ

Открой ветку `codex/v6.37.0`, нажми зелёную кнопку **Code**, затем **Download ZIP**.

Прямая ссылка на полный архив ветки:

<https://github.com/Arrrtemka246/Witch_tetris-git-/archive/refs/heads/codex/v6.37.0.zip>

Архив создаётся самим GitHub из полного дерева коммита. В нём находятся `main.py`, все 15 мини-игр, музыка, озвучка, кат-сцены, спрайты, секретные материалы, документы и тесты.

## Запуск на macOS

```bash
cd Witch_tetris-git--codex-v6.37.0
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

## Проверка полноты

После распаковки в корне должен находиться `RELEASE_MANIFEST_SHA256.txt`. Проверка на macOS:

```bash
shasum -a 256 -c RELEASE_MANIFEST_SHA256.txt
```

Сам `RELEASE_MANIFEST_SHA256.txt` не включает собственную контрольную сумму. Локальные файлы сохранений могут закономерно отличаться после запуска игры.
