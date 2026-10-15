from PySide6.QtWidgets import QWidget
from ui_game_window import Ui_GameWindow
from PySide6 import QtCore

class GameWindow(QWidget):
  def __init__(self, title_window):
    QWidget.__init__(self)
    self.__ui = Ui_GameWindow()
    self.__ui.setupUi(self)

    self.__tw = title_window

    self.__ui.pushButton_backToTitle.clicked.connect(self.__do_back_to_title)

  @QtCore.Slot()
  def __do_back_to_title(self):
    self.__tw.show()
    self.close()
