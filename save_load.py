"""save/load dialog window and
    routines to work with savedatas."""

from dataclasses import dataclass
from enum import Enum
import enum
from typing import override
import math

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QResizeEvent, QPixmap
from PySide6.QtWidgets import (QDialog,
                               QWidget,
                               QVBoxLayout,
                               QHBoxLayout,
                               QButtonGroup,
                               QToolButton,
                               QGridLayout,
                               QDialogButtonBox,
                               QFrame,
                               QLabel,
                               QSizePolicy,
                               QScrollArea)

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

class TopCenteredKeepRatioImageWidget(QLabel):
  """acknowledgements:
  implementation is largely inspired by:
  https://stackoverflow.com/questions/8211982/qt-resizing-a-qlabel-containing-a-qpixmap-while-keeping-its-aspect-ratio/43936590#43936590"""

  def __init__(self):
    QLabel.__init__(self)

    self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
    self.setScaledContents(True)

  def __fixup_ratio(self, widget_size: QSize, pixmap: QPixmap):
    if widget_size.isEmpty() or pixmap.isNull():
      self.setContentsMargins(0, 0, 0, 0)
      return

    pixmap_w, pixmap_h = pixmap.width(), pixmap.height()
    widget_w, widget_h = widget_size.width(), widget_size.height()

    x = max(pixmap_w / widget_w, pixmap_h / widget_h)
    scaled_w, scaled_h = pixmap_w / x, pixmap_h / x

    margin_v = math.floor(widget_h - scaled_h)
    margin_h = math.floor((widget_w - scaled_w) / 2)

    self.setContentsMargins(
      margin_h,  # left
      0,  # top
      margin_h,  # right
      margin_v  # bottom
    )

  @override
  def resizeEvent(self, event: QResizeEvent):
    self.__fixup_ratio(event.size(), self.pixmap())
    QLabel.resizeEvent(self, event)

  @override
  def setPixmap(self, pixmap: QPixmap):
    QLabel.setPixmap(self, pixmap)
    self.__fixup_ratio(self.size(), pixmap)

class SavedataSlotWidget(QFrame):
  def __init__(self):
    QFrame.__init__(self)
    self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)

    # Breeze Qt style from KDE Plasma 6 has broken StyledPanel upstream
    #   https://bugs.kde.org/show_bug.cgi?id=488195
    #
    # some KDE apps internally restore old behavior using a property
    #   https://github.com/KDE/breeze/blob/ef63411/kstyle/breezestyle.cpp#L685
    #
    # without this, StyledPanel does nothing at all on KDE Plasma 6.
    self.setProperty('_breeze_force_frame', True)

    self.__layout = QHBoxLayout()

    self.__image_widget = TopCenteredKeepRatioImageWidget()
    self.__layout.addWidget(self.__image_widget, 2)

    self.__details_layout = QVBoxLayout()

    self.__title_text_area = QScrollArea()
    self.__title_text_area.setWidgetResizable(True)
    self.__title_text_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
    self.__title_text_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    title_text_label = QLabel()
    title_text_label.setWordWrap(True)
    title_text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    self.__title_text_area.setWidget(title_text_label)

    self.__details_layout.addWidget(self.__title_text_area, 1)

    self.__date_label = QLabel()
    self.__details_layout.addWidget(self.__date_label, 0)

    self.__layout.addLayout(self.__details_layout, 5)

    self.__button_layout = QVBoxLayout()

    self.__button_layout.addStretch(1)

    self.__delete_button = QToolButton()
    self.__delete_button.setText('✘')
    self.__delete_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.__button_layout.addWidget(self.__delete_button, 0)

    self.__layout.addLayout(self.__button_layout, 0)

    self.setLayout(self.__layout)

_N_PAGES = 10
_N_ROWS = _N_COLS = 3

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

    for j in range(_N_ROWS):
      for i in range(_N_COLS):
        ssw = SavedataSlotWidget()
        self.__grid.addWidget(ssw, j, i)

    for i in range(_N_COLS):
      self.__grid.setColumnStretch(i, 1)

    for i in range(_N_ROWS):
      self.__grid.setRowStretch(i, 1)

    self.__dialog_buttons = QDialogButtonBox(standardButtons=QDialogButtonBox.StandardButton.Cancel)
    self.__layout.addWidget(self.__dialog_buttons, 0)
