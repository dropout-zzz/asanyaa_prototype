from PySide6.QtWidgets import QApplication
from title import TitleForm

def main():
  app = QApplication()
  tf = TitleForm(app)
  tf.show()
  app.exec()

main()
