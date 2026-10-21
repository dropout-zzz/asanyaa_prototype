"""save/load dialog window and
    routines to work with savedatas."""

from dataclasses import dataclass
from enum import Enum
import enum

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog,
                               QWidget,
                               QVBoxLayout,
                               QHBoxLayout,
                               QButtonGroup,
                               QToolButton,
                               QGridLayout,
                               QDialogButtonBox)

@dataclass
class SavedState:
  visible_dialogue_text_id: int | None = None
  visible_face_cg_id: int | None = None
  playing_background_music_id: int | None = None
  looping_sound_effect_id: int | None = None
  visible_background_cg_id: int | None = None

class PageButtons(QWidget):
  def __init__(self, n: int):
    QWidget.__init__(self)

    self.__layout = QHBoxLayout()
    self.setLayout(self.__layout)

    self.__layout.addStretch(1)

    self.__button_group = QButtonGroup(self)
    for i in range(n):
      button = QToolButton()
      button.setText(str(i + 1))
      button.setCheckable(True)
      button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
      self.__button_group.addButton(button, i)
      self.__layout.addWidget(button, 0)

    i = n - 1
    button_width = self.__button_group.button(i).sizeHint().width()
    i -= 1
    while not i < 0:
      self.__button_group.button(i).setFixedWidth(button_width)
      i -= 1

    self.__button_group.button(0).setChecked(True)

_N_PAGES = 10

class SaveLoadWindow(QDialog):
  class Mode(Enum):
    SAVE = enum.auto()
    LOAD = enum.auto()

  def __init__(self, parent: QWidget, mode: Mode):
    QDialog.__init__(self, parent)
    self.resize(1280, 720)

    match mode:
      case self.Mode.LOAD:
        self.setWindowTitle('Load')
      case self.Mode.SAVE:
        self.setWindowTitle('Save')

    self.__layout = QVBoxLayout()
    self.setLayout(self.__layout)

    self.__page_buttons = PageButtons(_N_PAGES)
    self.__layout.addWidget(self.__page_buttons, 0)

    self.__grid = QGridLayout()
    self.__layout.addLayout(self.__grid, 1)

    self.__dialog_buttons = QDialogButtonBox(standardButtons=QDialogButtonBox.StandardButton.Cancel)
    self.__layout.addWidget(self.__dialog_buttons, 0)
