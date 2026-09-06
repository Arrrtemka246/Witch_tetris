#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Install Python 3.12 from python.org, then run again.'
  read -r -p 'Press Enter...'
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv || exit 1
fi
if ! .venv/bin/python -c 'import pygame' >/dev/null 2>&1; then
  .venv/bin/python -m pip install -r requirements.txt || exit 1
fi
.venv/bin/python main.py
read -r -p 'Game closed. Press Enter...'
