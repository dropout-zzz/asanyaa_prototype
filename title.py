# -- qt
from PySide6 import QtCore
from PySide6.QtWidgets import (QWidget,
                               QApplication,
                               QDialog)

# -- qt generated
from ui_title import Ui_TitleForm

# -- project modules
from game_window import GameWindow
from act import load_act
from script import load_script, ScriptExecutor
from foo import Foo
from save_load import SaveLoadWindow

class TitleForm(QWidget):
  """title screen.
     when user starts a game, TitleForm is hidden."""

  def __init__(self,
               qapplication: QApplication,
               asset_root: str,
               savedata_root: str,
               foo: Foo):
    QWidget.__init__(self)
    self.__ui = Ui_TitleForm()
    self.__ui.setupUi(self)

    # -- private variables
    self.__qapp = qapplication
    self.__gw = None
    self.__asset_root = asset_root
    self.__savedata_root = savedata_root
    self.__foo = foo

    self.__ui.pushButton_quit.clicked.connect(self.__do_quit)
    self.__ui.pushButton_newGame.clicked.connect(self.__do_new_game)
    self.__ui.pushButton_loadGame.clicked.connect(self.__do_load_game)

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
                           self.__asset_root,
                           self.__savedata_root)
    self.__gw.show()
    self.close()
    self.__gw.run_until_no_more_script()

  @QtCore.Slot()
  def __do_load_game(self):
    slw = SaveLoadWindow(self,
                         SaveLoadWindow.Mode.LOAD,
                         self.__asset_root,
                         self.__savedata_root)
    if slw.exec() == QDialog.DialogCode.Accepted:
      sd = slw.get_selected_savedata()
      act = load_act(self.__asset_root, sd.act_letter)
      script = load_script(self.__asset_root,
                           sd.act_letter,
                           sd.script_id,
                           sd.script_sub_id)
      executor = ScriptExecutor(act,
                                script,
                                sd.instruction_pos,
                                self.__asset_root)
      self.__gw = GameWindow(self,
                             None,
                             self.__foo,
                             self.__asset_root,
                             self.__savedata_root)
      self.__gw.restore_from_state(GameWindow.State.from_saved_state(sd.state),
                                   executor)
      self.__gw.show()
      self.close()
      self.__gw.run_until_no_more_script()

  # --- qt callbacks end ---
