from PySide6.QtWidgets import QWidget, QApplication
from ui_title import Ui_TitleForm
from PySide6 import QtCore
from game_window import GameWindow
from act import load_act
from script import load_script

class TitleForm(QWidget):
  def __init__(self, qapplication: QApplication, asset_root: str):
    QWidget.__init__(self)
    self.__ui = Ui_TitleForm()
    self.__ui.setupUi(self)

    self.__qapp = qapplication
    self.__gw = None
    self.__asset_root = asset_root

    self.__ui.pushButton_quit.clicked.connect(self.__do_quit)
    self.__ui.pushButton_newGame.clicked.connect(self.__do_new_game)

  @QtCore.Slot()
  def __do_quit(self):
    self.__qapp.quit()

  @QtCore.Slot()
  def __do_new_game(self):
    # TODO: load ACT_A and 0000_00, use it to construct a fresh script executor at instruction #0 and feed it into GameWindow
    act = load_act(self.__asset_root, 'A')
    script = load_script(self.__asset_root, 'A', 0, 0)
    self.__gw = GameWindow(self)
    self.__gw.show()
    self.close()
