# -- py std
from typing import override
import re
from dataclasses import dataclass

# -- qt
from PySide6 import QtCore
from PySide6.QtCore import Qt, QEventLoop, QUrl
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import (QWidget,
                               QDialog,
                               QVBoxLayout,
                               QLabel,
                               QPushButton,
                               QMessageBox,
                               QButtonGroup)
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

# -- qt generated
from ui_game_window import Ui_GameWindow

# -- project modules
from script import ScriptExecutor, PlayMovieFlag
from foo import Foo
from utils import resolve_path_case_insensitive
from save_load import SavedState

class SelectionDialog(QDialog):
  def __init__(self, parent: QWidget, prompt: str, choices: list[str]):
    QDialog.__init__(self, parent)
    self.setWindowTitle('Choice')

    self.__button_group = QButtonGroup(self)
    self.__button_group.idClicked.connect(self.__handle_button_clicked)

    self.__layout = QVBoxLayout()
    self.__layout.addWidget(QLabel(prompt))
    for i, choice in enumerate(choices):
      btn = QPushButton(choice)
      self.__button_group.addButton(btn, i)
      self.__layout.addWidget(btn)
    self.setLayout(self.__layout)

    self.__selected = -1

  @QtCore.Slot(int)
  def __handle_button_clicked(self, button_idx: int):
    self.__selected = button_idx
    self.accept()

  def get_selected(self) -> int:
    return self.__selected

class MovieWindow(QDialog):
  def __init__(self,
               parent: QWidget,
               video_path: str,
               foo: Foo,
               user_skippable: bool = True):
    QDialog.__init__(self, parent)
    self.setWindowTitle('Movie')
    self.resize(1280, 720)

    self.__layout = QVBoxLayout()
    self.__layout.setContentsMargins(0, 0, 0, 0)
    self.__vw = QVideoWidget()
    self.__vw.videoSink().videoSizeChanged.connect(self.__handle_video_size_change)
    self.__layout.addWidget(self.__vw)
    self.setLayout(self.__layout)

    # -- private variables
    self.__foo = foo
    self.__user_skippable = user_skippable

    self.__ao = QAudioOutput(self, volume=0.30)
    self.__mp = QMediaPlayer(self,
                             audioOutput=self.__ao,
                             videoOutput=self.__vw,
                             source=QUrl.fromLocalFile(video_path))

    self.__mp.errorOccurred.connect(self.__handle_player_error)
    self.__mp.mediaStatusChanged.connect(self.__handle_player_media_status_change)

    self.finished.connect(self.__handle_dialog_finished)

  # -- overriden methods

  @override
  def mousePressEvent(self, event: QMouseEvent):
    if self.__user_skippable and event.button() == Qt.MouseButton.LeftButton:
      event.accept()
      self.accept()
      return
    QDialog.mousePressEvent(self, event)

  # -- qt callbacks

  @QtCore.Slot()
  def __handle_video_size_change(self):
    self.resize(self.__vw.videoSink().videoSize())

  @QtCore.Slot(QMediaPlayer.Error, str)
  def __handle_player_error(self, error: QMediaPlayer.Error, errorString: str):
    QMessageBox.warning(self,
                        self.__foo.system_messages.strings['errSystemError'],
                        self.__foo.system_messages.strings['mvLoadFailure'])
    self.reject()

  @QtCore.Slot(QMediaPlayer.MediaStatus)
  def __handle_player_media_status_change(self, status: QMediaPlayer.MediaStatus):
    match status:
      case QMediaPlayer.MediaStatus.EndOfMedia:
        self.accept()

  @QtCore.Slot(int)
  def __handle_dialog_finished(self, result: int):
    self.__mp.stop()

  # -- public methods

  def begin_playback(self):
    self.__mp.play()

_UNESCAPES: dict[str, str] = {r'\n': '\n', '&heart;': '❤'}
_ESCAPES = re.compile('|'.join(map(re.escape, _UNESCAPES.keys())))

def _get_unescaped(m: re.Match) -> str:
  return _UNESCAPES[m.group(0)]

class GameWindow(QWidget):
  @dataclass
  class State:
    current_dialogue_text_id: int | None = None
    current_face_cg_id: int | None = None
    current_background_music_id: int | None = None
    current_sound_effect_id: int | None = None
    current_background_cg_id: int | None = None

    @classmethod
    def from_saved_state(cls, saved_state: SavedState):
      gw_state = cls()

      gw_state.current_dialogue_text_id = saved_state.visible_dialogue_text_id
      gw_state.current_face_cg_id = saved_state.visible_face_cg_id
      gw_state.current_background_music_id = saved_state.playing_background_music_id
      gw_state.current_sound_effect_id = saved_state.looping_sound_effect_id
      gw_state.current_background_cg_id = saved_state.visible_background_cg_id

      return gw_state

  def __init__(self,
               title_window: QWidget,
               script_executor: ScriptExecutor,
               foo: Foo,
               asset_root: str):
    QWidget.__init__(self)
    self.__ui = Ui_GameWindow()
    self.__ui.setupUi(self)

    # -- private variables
    self.__tw = title_window
    self.__executor = script_executor
    self.__dialogue_wait_event_loop: QEventLoop | None = None
    self.__foo = foo
    self.__asset_root = asset_root
    self.__state = self.State()

    self.__ao_voice = QAudioOutput(self)
    self.__mp_voice = QMediaPlayer(self, audioOutput=self.__ao_voice)

    self.__ao_bgm = QAudioOutput(self, volume=0.20)
    self.__mp_bgm = QMediaPlayer(self,
                                 audioOutput=self.__ao_bgm,
                                 loops=QMediaPlayer.Loops.Infinite)

    self.__ao_sfx = QAudioOutput(self, volume=0.50)
    self.__mp_sfx = QMediaPlayer(self, audioOutput=self.__ao_sfx)

    self.__ui.pushButton_backToTitle.clicked.connect(self.__do_back_to_title)

    # --- register callbacks start ---

    self.__executor.set_ask_choices_callback(self.__handle_ask_choices)
    self.__executor.set_show_dialogue_wait_callback(self.__handle_show_dialogue_wait)
    self.__executor.set_set_face_cg_callback(self.__handle_set_face_cg)

    self.__executor.set_play_bgm_callback(self.__handle_play_bgm)
    self.__executor.set_fade_in_bgm_callback(self.__handle_play_bgm)
    self.__executor.set_fade_out_bgm_callback(self.__handle_stop_bgm)
    self.__executor.set_stop_bgm_callback(self.__handle_stop_bgm)

    self.__executor.set_play_sfx_callback(self.__handle_play_sfx)
    self.__executor.set_play_sfx_loop_callback(self.__handle_play_sfx_loop)
    self.__executor.set_fade_out_sfx(self.__handle_fade_out_sfx)

    self.__executor.set_play_movie_callback(self.__handle_play_movie)
    self.__executor.set_switch_background_callback(self.__handle_switch_background)

    # --- register callbacks end ---

  # --- overridden methods start ---

  @override
  def closeEvent(self, event):
    self.__cleanup()
    self.__executor = None
    QWidget.closeEvent(self, event)

  @override
  def mousePressEvent(self, event: QMouseEvent):
    if event.button() == Qt.MouseButton.LeftButton and self.__has_pending_dialogue():
      # progress the dialogue
      self.__abort_pending_dialogue()
      event.accept()
      return
    QWidget.mousePressEvent(self, event)

  # --- overridden methods end ---

  # --- public methods start ---

  def run_until_no_more_script(self):
    while self.__executor is not None:
      self.__executor.continue_execution()

  def restore_from_state(self, state: State, executor: ScriptExecutor):
    """intentionally not placing these logics in __init__() to
        allow loading savedata without re-creating GameWindow."""

    self.__cleanup()

    # -- extra UI resetting

    self.__ui.label_nameTag.clear()
    self.__ui.label_dialogueText.clear()
    self.__ui.label_background.clear()
    self.__ui.label_faceImageArea.clear()

    # --
    self.__state = state
    self.__executor = executor

    # -- now actually restore UI

    if state.current_dialogue_text_id is not None:
      name_tag, text = self.__resolve_text_id(state.current_dialogue_text_id)
      self.__ui.label_nameTag.setText(name_tag)
      self.__ui.label_dialogueText.setText(text)

    if state.current_face_cg_id is not None:
      self.__set_face_cg(state.current_face_cg_id)

    if state.current_background_music_id is not None:
      bgm_path = self.__construct_bgm_path(state.current_background_music_id)
      self.__mp_bgm.setSource(QUrl.fromLocalFile(bgm_path))
      self.__mp_bgm.play()

    if state.current_sound_effect_id is not None:
      sfx_path = self.__construct_sfx_path(state.current_sound_effect_id)
      self.__mp_sfx.setSource(QUrl.fromLocalFile(sfx_path))
      self.__mp_sfx.setLoops(QMediaPlayer.Loops.Infinite)
      self.__mp_sfx.play()

    if state.current_background_cg_id is not None:
      self.__set_background(state.current_background_cg_id)

  # --- public methods end ---

  # --- private methods start ---

  def __construct_sfx_path(self, sound_effect_id: int) -> str:
    sfx_name = self.__foo.se_tbl.rows[sound_effect_id][0]
    return resolve_path_case_insensitive(self.__asset_root, 'SE', sfx_name)

  def __resolve_text_id(self, text_id: int) -> tuple[str, str]:
    act = self.__executor.get_act()

    text_info = act.str_info[text_id]
    txd_off = text_info.offset_in_txd
    portion = act.strtab[txd_off:txd_off + text_info.length]
    name_tag, text_escaped = portion.decode('utf-8').split(',', 1)
    text = _ESCAPES.sub(_get_unescaped, text_escaped)

    return name_tag, text

  def __has_pending_dialogue(self) -> bool:
    return self.__dialogue_wait_event_loop is not None

  def __abort_pending_dialogue(self):
    event_loop = self.__dialogue_wait_event_loop
    self.__dialogue_wait_event_loop = None
    event_loop.quit()

  def __cleanup(self):
    self.__executor.stop()

    if self.__has_pending_dialogue():
      self.__abort_pending_dialogue()

    self.__mp_voice.stop()
    self.__mp_bgm.stop()
    self.__mp_sfx.stop()

  def __set_face_cg(self, cg_index: int):
    fcg_name = self.__foo.bmp_tbl.rows[cg_index][0].removesuffix('.kg')
    file_path = resolve_path_case_insensitive(self.__asset_root,
                                              'FCG',
                                              f'{fcg_name}.png')
    self.__ui.label_faceImageArea.setPixmap(QPixmap(file_path, format='PNG'))

  def __construct_bgm_path(self, background_music_id: int) -> str:
    bgm_name = self.__foo.bgm_tbl.rows[background_music_id][0]
    return resolve_path_case_insensitive(self.__asset_root, 'BGM', bgm_name)

  def __set_background(self, cg_index: int):
    file_name = self.__foo.bmp_tbl.rows[cg_index][0]
    file_path = resolve_path_case_insensitive(self.__asset_root, 'CG', file_name)
    self.__ui.label_background.setPixmap(QPixmap(file_path, format='BMP'))

  # --- private methods end ---

  # --- qt callbacks start ---

  @QtCore.Slot()
  def __do_back_to_title(self):
    self.__tw.show()
    self.close()

  # --- qt callbacks end ---

  # --- executor callbacks start ---

  def __handle_ask_choices(self, prompt_text_id: int, choice_text_ids: list[int]) -> int:
    _, prompt = self.__resolve_text_id(prompt_text_id)
    choices = [ self.__resolve_text_id(x)[1] for x in choice_text_ids ]

    while True:
      dlg = SelectionDialog(self, prompt, choices)
      if dlg.exec() == QDialog.DialogCode.Rejected:
        continue
      selected = dlg.get_selected()
      if selected < 0:
        continue
      return selected

  def __handle_show_dialogue_wait(self,
                                  text_id: int,
                                  character_id: int,
                                  voice_id: int):
    name_tag, text = self.__resolve_text_id(text_id)
    self.__ui.label_nameTag.setText(name_tag)
    self.__ui.label_dialogueText.setText(text)
    self.__state.current_dialogue_text_id = text_id

    cv_div = 0
    for n in self.__foo.cv_div.get(character_id, []):
      if voice_id < n:
        break
      cv_div += 1

    if cv_div > 0:
      voice_folder_name = f'CV{character_id:02}_{cv_div}'
    else:
      voice_folder_name = f'CV{character_id:02}'

    try:
      voice_path = resolve_path_case_insensitive(self.__asset_root,
                                                 voice_folder_name,
                                                 f'{voice_id:04}.ogg')
    except FileNotFoundError:
      pass
    else:
      self.__mp_voice.setSource(QUrl.fromLocalFile(voice_path))
      self.__mp_voice.play()

    if self.__dialogue_wait_event_loop is not None:
      raise RuntimeError
    self.__dialogue_wait_event_loop = QEventLoop(self)
    self.__dialogue_wait_event_loop.exec()

  def __handle_set_face_cg(self, cg_index: int):
    if cg_index < 0:
      self.__ui.label_faceImageArea.clear()
      self.__state.current_face_cg_id = None
      return

    self.__set_face_cg(cg_index)
    self.__state.current_face_cg_id = cg_index

  #   --- bgm start ---

  def __handle_play_bgm(self, background_music_id: int):
    bgm_path = self.__construct_bgm_path(background_music_id)
    self.__mp_bgm.setSource(QUrl.fromLocalFile(bgm_path))
    self.__mp_bgm.play()
    self.__state.current_background_music_id = background_music_id

  def __handle_stop_bgm(self):
    self.__mp_bgm.stop()
    self.__state.current_background_music_id = None

  #   --- bgm end ---

  #   --- sfx start ---

  def __handle_play_sfx(self, sound_effect_id: int):
    self.__mp_sfx.setSource(QUrl.fromLocalFile(self.__construct_sfx_path(sound_effect_id)))
    self.__mp_sfx.setLoops(QMediaPlayer.Loops.Once)
    self.__mp_sfx.play()
    self.__state.current_sound_effect_id = None

  def __handle_play_sfx_loop(self, sound_effect_id: int):
    self.__mp_sfx.setSource(QUrl.fromLocalFile(self.__construct_sfx_path(sound_effect_id)))
    self.__mp_sfx.setLoops(QMediaPlayer.Loops.Infinite)
    self.__mp_sfx.play()
    self.__state.current_sound_effect_id = sound_effect_id

  def __handle_fade_out_sfx(self):
    self.__mp_sfx.stop()
    self.__state.current_sound_effect_id = None

  #   --- sfx end ---

  def __handle_play_movie(self, movie_id: int, play_movie_flags: PlayMovieFlag):
    movie_file_name = self.__foo.movie_tbl.rows[movie_id][0]
    movie_path = resolve_path_case_insensitive(self.__asset_root, movie_file_name)

    dlg = MovieWindow(self,
                      movie_path,
                      self.__foo,
                      PlayMovieFlag.USER_UNSKIPPABLE in play_movie_flags)
    dlg.begin_playback()
    dlg.exec()

  def __handle_switch_background(self, cg_index: int, transition_effect_id: int):
    self.__set_background(cg_index)
    self.__state.current_background_cg_id = cg_index
