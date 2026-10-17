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
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtCore import QUrl
from utils import resolve_path_case_insensitive
from script import PlayMovieFlag
from PySide6.QtMultimediaWidgets import QVideoWidget

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

class MovieWindow(QDialog):
  def __init__(self, parent: QWidget, video_path: str):
    QDialog.__init__(self, parent)
    self.setWindowTitle('Movie')
    self.resize(1280, 720)

    self.__layout = QVBoxLayout()
    self.__layout.setContentsMargins(0, 0, 0, 0)
    self.__vw = QVideoWidget()
    self.__vw.videoSink().videoSizeChanged.connect(self.__handle_video_size_change)
    self.__layout.addWidget(self.__vw)
    self.setLayout(self.__layout)

    self.__ao = QAudioOutput(parent=self, volume=0.30)
    self.__mp = QMediaPlayer(parent=self,
                             audioOutput=self.__ao,
                             videoOutput=self.__vw,
                             source=QUrl.fromLocalFile(video_path))

  @QtCore.Slot()
  def __handle_video_size_change(self):
    self.resize(self.__vw.videoSink().videoSize())

  def begin_playback(self):
    self.__mp.play()

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

    self.__ao_voice = QAudioOutput(parent=self)
    self.__mp_voice = QMediaPlayer(parent=self, audioOutput=self.__ao_voice)

    self.__ao_bgm = QAudioOutput(parent=self, volume=0.20)
    self.__mp_bgm = QMediaPlayer(parent=self,
                                 audioOutput=self.__ao_bgm,
                                 loops=QMediaPlayer.Loops.Infinite)

    self.__ao_sfx = QAudioOutput(parent=self, volume=0.50)
    self.__mp_sfx = QMediaPlayer(parent=self, audioOutput=self.__ao_sfx)

    self.__ui.pushButton_backToTitle.clicked.connect(self.__do_back_to_title)

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

  @override
  def closeEvent(self, event):
    self.__executor.stop()
    if self.__dialogue_wait_event_loop is not None:
      event_loop = self.__dialogue_wait_event_loop
      self.__dialogue_wait_event_loop = None
      event_loop.quit()

    self.__mp_voice.stop()
    self.__mp_bgm.stop()
    self.__mp_sfx.stop()

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

    cv_div = 0
    for n in self.__foo.cv_div.get(character_id, []):
      if voice_id < n:
        break
      cv_div += 1

    voice_folder_name = f'CV{character_id:02}_{cv_div}' if cv_div > 0 else f'CV{character_id:02}'
    try:
      voice_path = resolve_path_case_insensitive(self.__asset_root, voice_folder_name, f'{voice_id:04}.ogg')
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
      return

    fcg_name = self.__foo.bmp_tbl.rows[cg_index][0].removesuffix('.kg')
    file_path = resolve_path_case_insensitive(self.__asset_root, 'FCG', f'{fcg_name}.png')
    self.__ui.label_faceImageArea.setPixmap(QPixmap(file_path, format='PNG'))

  def __handle_play_bgm(self, background_music_id: int):
    bgm_name = self.__foo.bgm_tbl.rows[background_music_id][0]
    bgm_path = resolve_path_case_insensitive(self.__asset_root, 'BGM', bgm_name)
    self.__mp_bgm.setSource(QUrl.fromLocalFile(bgm_path))
    self.__mp_bgm.play()

  def __handle_stop_bgm(self):
    self.__mp_bgm.stop()

  def __construct_sfx_path(self, sound_effect_id: int) -> str:
    sfx_name = self.__foo.se_tbl.rows[sound_effect_id][0]
    return resolve_path_case_insensitive(self.__asset_root, 'SE', sfx_name)

  def __handle_play_sfx(self, sound_effect_id: int):
    self.__mp_sfx.setSource(QUrl.fromLocalFile(self.__construct_sfx_path(sound_effect_id)))
    self.__mp_sfx.setLoops(QMediaPlayer.Loops.Once)
    self.__mp_sfx.play()

  def __handle_play_sfx_loop(self, sound_effect_id: int):
    self.__mp_sfx.setSource(QUrl.fromLocalFile(self.__construct_sfx_path(sound_effect_id)))
    self.__mp_sfx.setLoops(QMediaPlayer.Loops.Infinite)
    self.__mp_sfx.play()

  def __handle_fade_out_sfx(self):
    self.__mp_sfx.stop()

  def __handle_play_movie(self, movie_id: int, play_movie_flags: PlayMovieFlag):
    movie_file_name = self.__foo.movie_tbl.rows[movie_id][0]
    movie_path = resolve_path_case_insensitive(self.__asset_root, movie_file_name)

    dlg = MovieWindow(self, movie_path)
    dlg.begin_playback()
    dlg.exec()
