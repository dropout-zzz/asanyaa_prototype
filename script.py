# script loader and executor

from dataclasses import dataclass
import dataclasses
import string
import io
import sys
from enum import IntEnum, Flag
import enum
import struct

from act import Act, ScriptType, load_act
from utils import resolve_path_case_insensitive

# --- script loader start ---

@dataclass
class Instruction:
  """an undecoded script instruction."""

  # instruction number.
  # see Opcode enumeration class.
  opcode: int = 0

  # arguments for this instruction.
  # this contains raw bytes of an
  #  array of 32-bit integers.
  # interpretations of these varies depending on
  #  value of opcode.
  arguments: bytes = b'\x00\x00\x00\x00' * 7

@dataclass
class Script:
  """a loaded .spt file. a game script file."""

  # identities of this script.
  letter: str = 'A'
  script_id: int = 0
  script_sub_id: int = 0

  # instructions of this script.
  instructions: list[Instruction] = dataclasses.field(default_factory=list)

def load_script(asset_root: str,
                letter: str,
                script_id: int,
                script_sub_id: int) -> Script:
  if len(letter) != 1 or letter not in string.ascii_uppercase:
    raise ValueError(f'not a script letter: {letter!r}')
  if script_id < 0 or script_sub_id < 0:
    raise ValueError('invalid script id or sub id passed')

  script = Script()
  script.letter = letter
  script.script_id = script_id
  script.script_sub_id = script_sub_id

  script_file_name = f'{letter}{script_id:04}_{script_sub_id:02}.spt'

  with open(resolve_path_case_insensitive(asset_root,
                                          'data',
                                          script_file_name), 'rb') as f:
    with io.BytesIO(f.read()) as buf:
      n_instruction = int.from_bytes(buf.read(4), sys.byteorder)
      if len(buf.getbuffer()) != 4 + n_instruction * 32:
        raise ValueError('bad file size')

      while n_instruction > 0:
        inst = Instruction()
        inst.opcode = int.from_bytes(buf.read(4), sys.byteorder)
        inst.arguments = buf.read(28)

        script.instructions.append(inst)
        n_instruction -= 1

  return script

# --- script loader end ---

class Opcode(IntEnum):
  """list of known instruction numbers."""

  # show a dialogue text to user.
  # also may play a character voice.
  #  (if the voice file can be found.)
  # based on user's settings, the voice can
  #  continue playing or be stopped when user
  #  progresses dialogue before voice finished playing.
  #  (this is called Voice Cut.)
  # if there is voice currently playing, this
  #  instruction replaces it with the new one (if exists),
  #  guaranteeing the new voice starts playback immediately.
  # if there is voice currently playing but arguments of
  #  this instruction point to a non-existing voice file,
  #  the currently playing voice is not stopped.
  #
  # this instruction completes when
  #  user progresses the dialogue.
  #
  # this is the only instruction allowed in
  #  a selection script.
  # in a selection script, the 1st dialogue becomes
  #  the prompt text, all subsequent dialogues are
  #  choices. when the end of selection script is
  #  reached, the list of selection is shown to user,
  #  and execution continues at a branch stored in
  #  current script's next sub script ID array based
  #  on user's selection.
  DIALOGUE = 0x01

  # -- background music
  # start a background music playback.
  # the music will be looped.
  # stop the playback with FADE_OUT_BGM or STOP_BGM.
  PLAY_BGM = 0x06
  # fade in and start background music playback.
  # the music will be looped.
  # stop the playback with FADE_OUT_BGM or STOP_BGM.
  FADE_IN_BGM = 0x07
  # fade out the currently playing background music and
  #  stop the playback.
  FADE_OUT_BGM = 0x08
  # immediately stop the currently playing background music.
  STOP_BGM = 0x09

  # -- sound effects
  # play a sound effect once.
  # playback can be interrupted with FADE_OUT_SFX.
  PLAY_SFX = 0x0a
  # play a sound effect with looping.
  # stop the playback with FADE_OUT_SFX.
  PLAY_SFX_LOOP = 0x0b
  # fade out the currently playing sound effect.
  FADE_OUT_SFX = 0x0d

  # play a movie video.
  # this instruction completes when playback finishes.
  # any error is displayed to user if the game fails to
  #  play the video and this instruction completes.
  # the user may click the video area to skip the
  #  playback. then this instruction immediately finishes and
  #  the playback stops immediately.
  PLAY_MOVIE = 0x0f
  # switch to a new background image with
  #  a transition animation.
  SWITCH_BACKGROUND = 0x13
  # jump to next script immediately as if
  #  end of current script is reached.
  SKIP_TO_NEXT_SCRIPT = 0x24
  # show or hide character face icon next to the
  #  dialogue text displayed to user.
  # if face CG index is negative, it means to hide
  #  any currently shown face icon.
  CHANGE_FACE_CG = 0x2a

class PlayMovieFlag(Flag):
  """flags passed to PLAY_MOVIE callback."""

  # user may not skip the video playback by clicking the
  #  video area. by default, if this flag is not specified,
  #  the video is skippable.
  USER_UNSKIPPABLE = enum.auto()

class ScriptExecutor:
  """generic evaluator for game script.
     you should provide all callbacks using setter functions.
     depending on use case, you may want some of your
      callback implementation to wait for user action before returning.

     ScriptExecutor will simply ignore and skip through instruction when
      it sees any unknown opcode in instructions."""

  def __init__(self,
               act: Act,
               script: Script,
               instruction_pos: int,
               asset_root: str):
    """construct a script executor.
       the initial script and instruction position is passed on arguments.
       script executor loads subsequent scripts as needed automatically."""

    script_map_key = (script.script_id, script.script_sub_id)

    if act.letter != script.letter or script_map_key not in act.script_map:
      raise ValueError('unrelated script and act passed')
    self.__current_act = act
    self.__current_script = script

    self.__script_type = act.script_map[script_map_key].script_type
    if self.__script_type == ScriptType.SELECTION and instruction_pos > 0:
      raise ValueError('attempted to resume from middle of a selection script')
    if instruction_pos < 0 or instruction_pos > len(script.instructions) - 1:
      raise ValueError('not a instruction position')
    self.__current_instruction = instruction_pos

    # -- private variables
    self.__asset_root = asset_root
    self.__want_stop = False

    # -- selection
    self.__selection_prompt_text_id: int | None = None
    self.__choice_text_ids: list[int] = []

    # --- callbacks start ---

    self.__cb_ask_choices = None
    self.__cb_show_dialogue_wait = None
    self.__cb_set_face_cg = None

    self.__cb_play_bgm = None
    self.__cb_fade_in_bgm = None
    self.__cb_fade_out_bgm = None
    self.__cb_stop_bgm = None

    self.__cb_play_sfx = None
    self.__cb_play_sfx_loop = None
    self.__cb_fade_out_sfx = None

    self.__cb_play_movie = None
    self.__cb_switch_background = None

    # --- callbacks end ---

  # --- callback setters start ---

  def set_ask_choices_callback(self, fn):
    self.__cb_ask_choices = fn

  def set_show_dialogue_wait_callback(self, fn):
    self.__cb_show_dialogue_wait = fn

  def set_set_face_cg_callback(self, fn):
    self.__cb_set_face_cg = fn

  #   --- bgm callbacks start ---

  def set_play_bgm_callback(self, fn):
    self.__cb_play_bgm = fn

  def set_fade_in_bgm_callback(self, fn):
    self.__cb_fade_in_bgm = fn

  def set_fade_out_bgm_callback(self, fn):
    self.__cb_fade_out_bgm = fn

  def set_stop_bgm_callback(self, fn):
    self.__cb_stop_bgm = fn

  #   --- bgm callbacks end ---

  #   --- sfx callbacks start ---

  def set_play_sfx_callback(self, fn):
    self.__cb_play_sfx = fn

  def set_play_sfx_loop_callback(self, fn):
    self.__cb_play_sfx_loop = fn

  def set_fade_out_sfx(self, fn):
    self.__cb_fade_out_sfx = fn

  #   --- sfx callbacks end ---

  def set_play_movie_callback(self, fn):
    self.__cb_play_movie = fn

  def set_switch_background_callback(self, fn):
    self.__cb_switch_background = fn

  # --- callback setters end ---

  # --- public methods start ---

  def continue_execution(self):
    """run until stop() is requested.
       this method should only be called once for each instance."""

    while True:
      inst = self.__current_script.instructions[self.__current_instruction]

      if self.__script_type == ScriptType.SELECTION and inst.opcode != Opcode.DIALOGUE:
        raise ValueError('disallowed instruction in selection script')

      match inst.opcode:
        case Opcode.DIALOGUE:
          character_id, voice_id = struct.unpack('II', inst.arguments[:8])
          text_id = int.from_bytes(inst.arguments[-4:], sys.byteorder)

          if self.__script_type == ScriptType.SELECTION:
            if self.__selection_prompt_text_id is None:
              self.__selection_prompt_text_id = text_id
            else:
              self.__choice_text_ids.append(text_id)
              if len(self.__choice_text_ids) > 10:
                raise ValueError('too many selection choices')
          else:
            self.__cb_show_dialogue_wait(text_id, character_id, voice_id)

        case Opcode.CHANGE_FACE_CG:
          cg_index = int.from_bytes(inst.arguments[-4:], sys.byteorder, signed=True)
          self.__cb_set_face_cg(cg_index)

        # -- bgm instructions start --

        case Opcode.PLAY_BGM:
          background_music_id = int.from_bytes(inst.arguments[-4:], sys.byteorder)
          self.__cb_play_bgm(background_music_id)

        case Opcode.FADE_IN_BGM:
          background_music_id = int.from_bytes(inst.arguments[-4:], sys.byteorder)
          self.__cb_fade_in_bgm(background_music_id)

        case Opcode.FADE_OUT_BGM:
          self.__cb_fade_out_bgm()

        case Opcode.STOP_BGM:
          self.__cb_stop_bgm()

        # --- bgm instructions end ---

        # --- sfx instructions start ---

        case Opcode.PLAY_SFX:
          sound_effect_id = int.from_bytes(inst.arguments[-4:], sys.byteorder)
          self.__cb_play_sfx(sound_effect_id)

        case Opcode.PLAY_SFX_LOOP:
          sound_effect_id = int.from_bytes(inst.arguments[-4:], sys.byteorder)
          self.__cb_play_sfx_loop(sound_effect_id)

        case Opcode.FADE_OUT_SFX:
          self.__cb_fade_out_sfx()

        # --- sfx instructions end ---

        case Opcode.PLAY_MOVIE:
          with io.BytesIO(inst.arguments) as buf:
            buf.read(8)  # skip unk1
            flags = int.from_bytes(buf.read(4), sys.byteorder)

            play_movie_flags = PlayMovieFlag(0)

            if flags & 0b1:
              play_movie_flags |= PlayMovieFlag.USER_UNSKIPPABLE

            movie_id = int.from_bytes(inst.arguments[-4:], sys.byteorder)
            self.__cb_play_movie(movie_id, play_movie_flags)

        case Opcode.SWITCH_BACKGROUND:
          with io.BytesIO(inst.arguments) as buf:
            buf.read(16)  # skip unk1
            cg_index = int.from_bytes(buf.read(4), sys.byteorder)
            transition_effect_id = int.from_bytes(inst.arguments[-4:], sys.byteorder)
            self.__cb_switch_background(cg_index, transition_effect_id)

      if self.__want_stop:
        break

      self.__current_instruction += 1
      if self.__current_instruction == len(self.__current_script.instructions) \
         or inst.opcode == Opcode.SKIP_TO_NEXT_SCRIPT:
        script_map_key = (self.__current_script.script_id, self.__current_script.script_sub_id)
        desc = self.__current_act.script_map[script_map_key]
        if desc.next_script_letter != self.__current_act.letter:
          self.__current_act = load_act(self.__asset_root, desc.next_script_letter)
        if self.__script_type == ScriptType.SELECTION:
          if self.__selection_prompt_text_id is None:
            raise ValueError('missing selection prompt')
          if len(self.__choice_text_ids) == 0:
            raise ValueError('missing selection choices')
          selected = self.__cb_ask_choices(self.__selection_prompt_text_id, self.__choice_text_ids)
          next_script_sub_id = desc.next_script_sub_id[selected]
          if next_script_sub_id < 0:
            raise ValueError('missing valid jump target for choice')
        else:
          next_script_sub_id = desc.next_script_sub_id[0]
        self.__current_script = load_script(self.__asset_root,
                                            desc.next_script_letter,
                                            desc.next_script_id,
                                            next_script_sub_id)

        script_map_key = (desc.next_script_id, next_script_sub_id)
        next_script_type = self.__current_act.script_map[script_map_key].script_type
        self.__script_type = next_script_type
        if next_script_type == ScriptType.SELECTION:
          self.__selection_prompt_text_id = None
          self.__choice_text_ids.clear()
        self.__current_instruction = 0

  def stop(self):
    """request evaluation loop to stop.
       this method may be used in your callback implementation."""

    self.__want_stop = True

  # --- getters start ---

  def get_act(self) -> Act:
    """return Act instance allowing caller to
        use it to resolve text IDs."""
    return self.__current_act

  # return informations needed for
  #  caller to implement saving.
  def get_instruction_pos(self) -> int:
    """get current instruction position.
       this function returns meaningful value only when
        the evaluation loop is currently active.

       note that when called from callback implementation,
        this points to instruction currently being executed,
        rather than the next one."""
    return self.__current_instruction
  def get_script_id(self) -> int:
    return self.__current_script.script_id
  def get_script_sub_id(self) -> int:
    return self.__current_script.script_sub_id
  def get_act_letter(self) -> int:
    return self.__current_act.letter

  # --- getters end ---
