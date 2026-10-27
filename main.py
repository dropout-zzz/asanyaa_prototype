#!/usr/bin/env python
"""application entrypoint."""

import argparse
import os.path

from PySide6.QtWidgets import QApplication

from title import TitleForm
from foo import foo_init

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('asset_dir')
  ap.add_argument('savedata_dir')
  args = ap.parse_args()

  if not os.path.isdir(args.asset_dir):
    ap.error('specified asset directory doesnt exist')

  if not os.path.isdir(args.savedata_dir):
    ap.error('specified savedata directory doesnt exist')

  foo = foo_init(args.asset_dir)

  app = QApplication()
  tf = TitleForm(app,
                 args.asset_dir,
                 args.savedata_dir,
                 foo)
  tf.show()
  app.exec()

main()
