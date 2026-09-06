"""Developer preview: python preview_ending.py [--frames DIRECTORY]."""
import sys
from pathlib import Path
if '--frames' in sys.argv:
    import os
    os.environ.setdefault('SDL_VIDEODRIVER','dummy')
    os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from main import Game
from ending import Ending

game=Game()
game.ending=Ending()
if '--frames' in sys.argv:
    folder=Path(sys.argv[sys.argv.index('--frames')+1]); folder.mkdir(parents=True,exist_ok=True)
    for tick in (7,14,17,18,20,21,23,24,27,31):
        game.ending.draw(game.canvas,tick)
        pygame.image.save(game.canvas,str(folder/f'ending_{tick:02}.png'))
    pygame.quit()
else:
    game.ending.start(game)
    game.run()
