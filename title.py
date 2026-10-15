from PySide6.QtWidgets import QWidget, QApplication
from ui_title import Ui_TitleForm
from PySide6 import QtCore
from game_window import GameWindow

class TitleForm(QWidget):
  def __init__(self, qapplication: QApplication):
    QWidget.__init__(self)
    self.__ui = Ui_TitleForm()
    self.__ui.setupUi(self)

    self.__qapp = qapplication
    self.__gw = None

    self.__ui.pushButton_quit.clicked.connect(self.__do_quit)
    self.__ui.pushButton_startGame.clicked.connect(self.__do_start_game)

  @QtCore.Slot()
  def __do_quit(self):
    self.__qapp.quit()

  @QtCore.Slot()
  def __do_start_game(self):
    # TODO: load ACT_A and 0000_00, use it to construct a fresh script executor at instruction #0 and feed it into GameWindow
    self.__gw = GameWindow(self)
    self.__gw.show()
    self.close()
