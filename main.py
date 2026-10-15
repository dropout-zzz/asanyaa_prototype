from PySide6.QtWidgets import QApplication
from title import TitleForm
import argparse

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('asset_dir')
  args = ap.parse_args()

  app = QApplication()
  tf = TitleForm(app, args.asset_dir)
  tf.show()
  app.exec()

main()
