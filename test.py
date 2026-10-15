from PySide6.QtWidgets import QApplication, QWidget
from ui_title import Ui_TitleForm
from PySide6 import QtCore

class TitleForm(QWidget):
  def __init__(self):
    QWidget.__init__(self)
    self.__ui = Ui_TitleForm()
    self.__ui.setupUi(self)

    self.__ui.pushButton_quit.clicked.connect(self.__do_quit)

  @QtCore.Slot()
  def __do_quit(self):
    self.close()

def main():
  app = QApplication()
  tf = TitleForm()
  tf.show()
  app.exec()

main()
