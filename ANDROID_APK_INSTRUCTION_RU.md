# Как собрать APK — W.I.T.C.H. Tetris Android TEST

Это отдельная тестовая Android-ветка на базе **v6.17**. Она не заменяет основной desktop-код v6.17.

## Что уже подготовлено

В проекте уже есть `buildozer.spec`, локальный экспериментальный recipe `p4a-recipes/pygame-ce/` и touch-управление. Собирать надо debug APK.

## Вариант A — Linux / Ubuntu (самый предсказуемый)

Установить системные зависимости:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk autoconf automake autopoint \
  libtool pkg-config cmake ccache libffi-dev libssl-dev python3 python3-venv \
  python3-pip build-essential rustc
```

Создать окружение и поставить Buildozer:

```bash
python3 -m venv .venv-android
source .venv-android/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install "cython==0.29.34" legacy-cgi
python -m pip install git+https://github.com/kivy/buildozer
```

Перейти в распакованный проект и запустить:

```bash
buildozer -v android debug
```

Первый запуск скачивает Android SDK/NDK и поэтому обычно самый долгий. Готовый APK Buildozer кладёт в папку `bin/`.

## Вариант B — Mac M1/M2/M3

Buildozer допускает Android-сборку на macOS, но именно этот Pygame test-build использует экспериментальный pygame-ce recipe, поэтому Linux обычно предсказуемее. На Mac сначала нужны Xcode Command Line Tools, Homebrew, Java 17, autoconf/automake/libtool/pkg-config/cmake/ccache и Python venv, затем те же команды установки Buildozer и:

```bash
buildozer -v android debug
```

Если macOS-сборка упрётся в NDK/recipe, используй Linux/Colab-вариант ниже вместо изменения игрового кода.

## Вариант C — без ноутбука, через Google Colab с телефона

В архиве есть `WITCH_ANDROID_BUILD_COLAB.ipynb`. Его можно загрузить в Google Drive/Colab, открыть в Colab, затем выполнить ячейки по порядку. Ноутбук попросит загрузить ZIP этой Android-test сборки, установит системные зависимости, распакует проект и запустит Buildozer. После завершения последняя ячейка покажет APK из `bin/` и предложит скачать его.

Важно: первая Android-сборка тяжёлая и может не уложиться в бесплатную сессию Colab. Если сессия оборвётся, это не означает ошибку игры.

## Установка APK на телефон

Перед установкой Android может попросить разрешить установку приложений из текущего источника (браузер/Files). Разреши это только для собственного тестового APK, установи приложение, а после теста разрешение можно снова выключить.

## Если сборка упала

Сохрани последние ~100 строк Buildozer-лога. Наиболее вероятный источник проблемы здесь не игровой Python-код, а экспериментальная Android-сборка pygame-ce. Не надо переносить эти изменения в основной v6.17: пришли лог, и Android-test ветку можно чинить отдельно.
