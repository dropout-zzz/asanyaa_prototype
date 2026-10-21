"""save/load dialog window and
    routines to work with savedatas."""

from dataclasses import dataclass
from enum import Enum
import enum

from PySide6.QtWidgets import QDialog, QWidget

@dataclass
class SavedState:
  visible_dialogue_text_id: int | None = None
  visible_face_cg_id: int | None = None
  playing_background_music_id: int | None = None
  looping_sound_effect_id: int | None = None
  visible_background_cg_id: int | None = None

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
