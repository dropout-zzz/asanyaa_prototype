asanyaa_prototype
=================

an experiment for an alternate multi-platform implementation of Asanyaa game based on Qt and Python. may not be fully playable yet.

this doesn't yet strictly mirror the original game, it's not based on decompilation. i started this for learning Qt.

currently *.fpk archives must be unpacked into folders and *.kg files must be converted into PNG images beforehand (tools for doing so is not yet provided in this repository).

unimplemented features, and not planned yet:
- any animations, visual effects or transitions

so far this implementation uses its own savedata format based on JSON and is not compatible with the original game. it can't yet read savedatas from the original game.


INSTALLATION
============

- requires a modern version of Python 3 and PySide6.

- requires game assets from the original game.

- run `gen_ui_py_files.sh` after cloning the source code, game is started via `main.py`. you need to pass it a directory that contains unpacked and fixed up (e.g. all *.kg converted into *.png) game assets (each *.fpk should have a separate corresponding unpacked folder under the directory you pass).

code in this repository is provided under the GPL 3.0 terms, see more information in `COPYING.TXT`.
