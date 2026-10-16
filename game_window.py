from PySide6.QtWidgets import QWidget
from ui_game_window import Ui_GameWindow
from PySide6 import QtCore
from script import ScriptExecutor
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QEventLoop
from typing import override
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import Qt
from foo import Foo
import os.path
from PySide6.QtGui import QPixmap

class ChoiceButton(QPushButton):
  myCallback = QtCore.Signal(int)

  def __init__(self, text: str, idx: int):
    QPushButton.__init__(self, text)
    self.__idx = idx
    self.clicked.connect(self.__do_callback)

  @QtCore.Slot()
  def __do_callback(self):
    self.myCallback.emit(self.__idx)

class SelectionDialog(QDialog):
  def __init__(self, parent: QWidget, prompt: str, choices: list[str]):
    QDialog.__init__(self, parent)
    self.setWindowTitle('Choice')
    self.__layout = QVBoxLayout()
    self.__layout.addWidget(QLabel(prompt))
    for i, choice in enumerate(choices):
      btn = ChoiceButton(choice, i)
      btn.myCallback.connect(self.__do_callback)
      self.__layout.addWidget(btn)
    self.setLayout(self.__layout)

    self.__selected = -1

  @QtCore.Slot(int)
  def __do_callback(self, idx: int):
    self.__selected = idx
    self.accept()

  def get_selected(self) -> int:
    return self.__selected

class GameWindow(QWidget):
  def __init__(self, title_window: QWidget, script_executor: ScriptExecutor, foo: Foo, asset_root: str):
    QWidget.__init__(self)
    self.__ui = Ui_GameWindow()
    self.__ui.setupUi(self)

    self.__tw = title_window
    self.__executor = script_executor
    self.__dialogue_wait_event_loop: QEventLoop | None = None
    self.__foo = foo
    self.__asset_root = asset_root

    self.__ui.pushButton_backToTitle.clicked.connect(self.__do_back_to_title)

    self.__executor.set_ask_choices_callback(self.__handle_ask_choices)
    self.__executor.set_show_dialogue_wait_callback(self.__handle_show_dialogue_wait)
    self.__executor.set_set_face_cg_callback(self.__handle_set_face_cg)

  @override
  def closeEvent(self, event):
    self.__executor.stop()
    if self.__dialogue_wait_event_loop is not None:
      event_loop = self.__dialogue_wait_event_loop
      self.__dialogue_wait_event_loop = None
      event_loop.quit()
    QWidget.closeEvent(self, event)

  @override
  def mousePressEvent(self, event: QMouseEvent):
    if event.button() == Qt.MouseButton.LeftButton and self.__dialogue_wait_event_loop is not None:
      # progress the dialogue

      event_loop = self.__dialogue_wait_event_loop
      self.__dialogue_wait_event_loop = None
      event_loop.quit()
      event.accept()
      return
    QWidget.mousePressEvent(self, event)

  def init(self):
    self.__executor.continue_execution()

  @QtCore.Slot()
  def __do_back_to_title(self):
    self.__tw.show()
    self.close()

  def __handle_ask_choices(self, prompt: str, choices: list[str]) -> int:
    while True:
      dlg = SelectionDialog(self, prompt, choices)
      if dlg.exec() == QDialog.DialogCode.Rejected:
        continue
      selected = dlg.get_selected()
      if selected < 0:
        continue
      return selected

  def __handle_show_dialogue_wait(self, name_tag: str, text: str, character_id: int, voice_id: int):
    self.__ui.label_nameTag.setText(name_tag)
    self.__ui.label_dialogueText.setText(text)
    if self.__dialogue_wait_event_loop is not None:
      raise RuntimeError
    self.__dialogue_wait_event_loop = QEventLoop(self)
    self.__dialogue_wait_event_loop.exec()

  def __handle_set_face_cg(self, cg_index: int):
    if cg_index < 0:
      self.__ui.label_faceImageArea.clear()
      return

    fcg_name = self.__foo.bmp_tbl.rows[cg_index][0].removesuffix('.kg')
    file_path = os.path.join(self.__asset_root, 'FCG', f'{fcg_name}.png')
    self.__ui.label_faceImageArea.setPixmap(QPixmap(file_path, format='PNG'))
