#!/usr/bin/env python

from PySide6.QtWidgets import QApplication
from title import TitleForm
import argparse
from foo import foo_init
import os.path

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('asset_dir')
  args = ap.parse_args()

  if not os.path.isdir(args.asset_dir):
    ap.error('specified asset directory doesnt exist')

  foo = foo_init(args.asset_dir)

  app = QApplication()
  tf = TitleForm(app, args.asset_dir, foo)
  tf.show()
  app.exec()

main()
