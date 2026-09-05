# Как скачать W.I.T.C.H. Tetris v6.37.1

Открой ветку `codex/v6.37.1`, нажми зелёную кнопку **Code**, затем **Download ZIP**.

Прямая ссылка на полный архив:

<https://github.com/Arrrtemka246/Witch_tetris-git-/archive/refs/heads/codex/v6.37.1.zip>

Архив создаётся самим GitHub из полного дерева коммита и включает исходный код, 14 мини-игр, всю музыку, озвучку, кат-сцены, спрайты, секретные материалы, документацию и тесты.

## Запуск на macOS

```bash
cd Witch_tetris-git--codex-v6.37.1
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

## Проверка полноты

```bash
shasum -a 256 -c RELEASE_MANIFEST_SHA256.txt
```

Сам файл манифеста не включает собственную контрольную сумму.
