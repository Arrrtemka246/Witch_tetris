"""Run on the target OS after installing requirements and pyinstaller."""
from pathlib import Path
import subprocess
import sys
import os
root=Path(__file__).resolve().parent
os.chdir(root)
args=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed','--name','WITCH_Tetris',
      '--add-data',f'assets{os.pathsep}assets','--add-data',f'ending_credits.txt{os.pathsep}.','main.py']
subprocess.run(args,check=True)
if sys.platform=='darwin':
    subprocess.run(['hdiutil','create','-volname','WITCH Tetris','-srcfolder','dist/WITCH_Tetris.app',
                    '-ov','-format','UDZO','dist/WITCH_Tetris.dmg'],check=True)
print('Build is in dist/. On Windows distribute the entire WITCH_Tetris directory.')
