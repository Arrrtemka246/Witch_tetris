from pathlib import Path

import pygame


APP_NAME = "Witch Tetris"
BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "build_assets" / "icon.png"


# ВАЖНО: ставим иконку ДО создания окна.
pygame.display.init()

if ICON_PATH.exists():
    try:
        icon = pygame.image.load(str(ICON_PATH))
        pygame.display.set_icon(icon)
    except pygame.error:
        pass


import main


def run():
    game = main.Game()

    # main.py устанавливает своё название, поэтому заменяем его после создания Game.
    pygame.display.set_caption(APP_NAME)

    # Не fullscreen.
    # Это обычное RESIZABLE-окно, просто разворачиваем его максимально.
    try:
        from pygame._sdl2.video import Window

        window = Window.from_display_module()
        window.maximize()
    except Exception:
        pass

    game.fullscreen = False
    game.run()


if __name__ == "__main__":
    run()
