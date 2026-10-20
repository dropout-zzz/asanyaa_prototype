"""save/load dialog window and
    routines to work with savedatas."""

from dataclasses import dataclass

@dataclass
class SavedState:
  visible_dialogue_text_id: int | None = None
  visible_face_cg_id: int | None = None
  playing_background_music_id: int | None = None
  looping_sound_effect_id: int | None = None
  visible_background_cg_id: int | None = None
