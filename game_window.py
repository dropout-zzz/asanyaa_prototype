from PySide6.QtWidgets import QWidget
from ui_game_window import Ui_GameWindow
from PySide6 import QtCore
from script import ScriptExecutor

class GameWindow(QWidget):
  def __init__(self, title_window: QWidget, script_executor: ScriptExecutor):
    QWidget.__init__(self)
    self.__ui = Ui_GameWindow()
    self.__ui.setupUi(self)

    self.__tw = title_window
    self.__executor = script_executor

    self.__ui.pushButton_backToTitle.clicked.connect(self.__do_back_to_title)

    # TODO: register script executor callbacks and continue execution
    self.__executor.set_ask_choices_callback(self.__handle_ask_choices)
    self.__executor.set_show_dialogue_wait_callback(self.__handle_show_dialogue_wait)

    self.__executor.continue_execution()

  @QtCore.Slot()
  def __do_back_to_title(self):
    self.__tw.show()
    self.close()

  def __handle_ask_choices(self, prompt: str, choices: list[str]) -> int:
    raise NotImplementedError

  def __handle_show_dialogue_wait(self, name_tag: str, text: str, character_id: int, voice_id: int):
    raise NotImplementedError
