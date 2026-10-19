# -- qt
from PySide6 import QtCore
from PySide6.QtWidgets import QWidget, QApplication

# -- qt generated
from ui_title import Ui_TitleForm

# -- project modules
from game_window import GameWindow
from act import load_act
from script import load_script, ScriptExecutor
from foo import Foo

class TitleForm(QWidget):
  def __init__(self,
               qapplication: QApplication,
               asset_root: str,
               foo: Foo):
    QWidget.__init__(self)
    self.__ui = Ui_TitleForm()
    self.__ui.setupUi(self)

    # -- private variables
    self.__qapp = qapplication
    self.__gw = None
    self.__asset_root = asset_root
    self.__foo = foo

    self.__ui.pushButton_quit.clicked.connect(self.__do_quit)
    self.__ui.pushButton_newGame.clicked.connect(self.__do_new_game)

  # --- qt callbacks start ---

  @QtCore.Slot()
  def __do_quit(self):
    self.__qapp.quit()

  @QtCore.Slot()
  def __do_new_game(self):
    act = load_act(self.__asset_root, 'A')
    script = load_script(self.__asset_root, 'A', 0, 0)
    executor = ScriptExecutor(act,
                              script,
                              0,
                              self.__asset_root)
    self.__gw = GameWindow(self,
                           executor,
                           self.__foo,
                           self.__asset_root)
    self.__gw.show()
    self.close()
    self.__gw.init()

  # --- qt callbacks end ---
