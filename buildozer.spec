[app]
title = W.I.T.C.H. Tetris Android Test
package.name = witchtetris_test
package.domain = org.openai.localtest
source.dir = .
source.include_exts = py,png,jpg,jpeg,webp,mp3,wav,ogg,flac,m4a,json,txt,md
source.exclude_dirs = .git,.venv,__pycache__,bin,.buildozer
version = 6.17.0-test1
requirements = python3,pygame-ce
orientation = portrait
fullscreen = 1

# No permissions are required for the game itself.
android.permissions =
android.api = 36
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a
android.accept_sdk_license = True

# pygame-ce is not an upstream p4a recipe yet; this test package vendors one.
p4a.local_recipes = ./p4a-recipes
p4a.branch = develop
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 0
