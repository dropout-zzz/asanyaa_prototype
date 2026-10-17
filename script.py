# script loader and executor

from dataclasses import dataclass
import dataclasses
import string
import os.path
import io
import sys
from act import Act
from act import ScriptType
from act import load_act
from enum import IntEnum
import struct
import re

@dataclass
class Instruction:
  opcode: int = 0
  arguments: bytes = b'\x00\x00\x00\x00' * 7

@dataclass
class Script:
  letter: str = 'A'
  script_id: int = 0
  script_sub_id: int = 0
  instructions: list[Instruction] = dataclasses.field(default_factory=list)

def load_script(asset_root: str, letter: str, script_id: int, script_sub_id: int) -> Script:
  if len(letter) != 1 or letter not in string.ascii_uppercase:
    raise ValueError(f'not a script letter: {letter!r}')
  if script_id < 0 or script_sub_id < 0:
    raise ValueError('invalid script id or sub id passed')

  script = Script()
  script.letter = letter
  script.script_id = script_id
  script.script_sub_id = script_sub_id

  with open(os.path.join(asset_root, 'data', f'{letter}{script_id:04}_{script_sub_id:02}.spt'), 'rb') as f:
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

class Opcode(IntEnum):
  DIALOGUE = 0x01
  PLAY_BGM = 0x06
  FADE_IN_BGM = 0x07
  FADE_OUT_BGM = 0x08
  STOP_BGM = 0x09
  PLAY_SFX = 0x0a
  PLAY_SFX_LOOP = 0x0b
  FADE_OUT_SFX = 0x0d
  CHANGE_FACE_CG = 0x2a

_UNESCAPES: dict[str, str] = {r'\n': '\n', '&heart;': '❤'}
_ESCAPES = re.compile('|'.join(map(re.escape, _UNESCAPES.keys())))

def _get_unescaped(m: re.Match) -> str:
  return _UNESCAPES[m.group(0)]

class ScriptExecutor:
  def __init__(self, act: Act, script: Script, instruction_pos: int, asset_root: str):
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

    self.__asset_root = asset_root
    self.__want_stop = False

    self.__selection_prompt: str | None = None
    self.__choices: list[str] = []

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

  def set_ask_choices_callback(self, fn):
    self.__cb_ask_choices = fn

  def set_show_dialogue_wait_callback(self, fn):
    self.__cb_show_dialogue_wait = fn

  def set_set_face_cg_callback(self, fn):
    self.__cb_set_face_cg = fn

  def set_play_bgm_callback(self, fn):
    self.__cb_play_bgm = fn

  def set_fade_in_bgm_callback(self, fn):
    self.__cb_fade_in_bgm = fn

  def set_fade_out_bgm_callback(self, fn):
    self.__cb_fade_out_bgm = fn

  def set_stop_bgm_callback(self, fn):
    self.__cb_stop_bgm = fn

  def set_play_sfx_callback(self, fn):
    self.__cb_play_sfx = fn

  def set_play_sfx_loop_callback(self, fn):
    self.__cb_play_sfx_loop = fn

  def set_fade_out_sfx(self, fn):
    self.__cb_fade_out_sfx = fn

  def continue_execution(self):
    while True:
      inst = self.__current_script.instructions[self.__current_instruction]

      if self.__script_type == ScriptType.SELECTION and inst.opcode != Opcode.DIALOGUE:
        raise ValueError('disallowed instruction in selection script')

      match inst.opcode:
        case Opcode.DIALOGUE:
          character_id, voice_id = struct.unpack('II', inst.arguments[:8])

          text_id = int.from_bytes(inst.arguments[-4:], sys.byteorder)
          text_info = self.__current_act.str_info[text_id]
          txd_off = text_info.offset_in_txd
          name_tag, text_escaped = self.__current_act.strtab[txd_off:txd_off + text_info.length].decode('utf-8').split(',', 1)
          text = _ESCAPES.sub(_get_unescaped, text_escaped)

          if self.__script_type == ScriptType.SELECTION:
            if self.__selection_prompt is None:
              self.__selection_prompt = text
            else:
              self.__choices.append(text)
              if len(self.__choices) > 10:
                raise ValueError('too many selection choices')
          else:
            self.__cb_show_dialogue_wait(name_tag, text, character_id, voice_id)

        case Opcode.CHANGE_FACE_CG:
          cg_index = int.from_bytes(inst.arguments[-4:], sys.byteorder, signed=True)
          self.__cb_set_face_cg(cg_index)

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

        case Opcode.PLAY_SFX:
          sound_effect_id = int.from_bytes(inst.arguments[-4:], sys.byteorder)
          self.__cb_play_sfx(sound_effect_id)

        case Opcode.PLAY_SFX_LOOP:
          sound_effect_id = int.from_bytes(inst.arguments[-4:], sys.byteorder)
          self.__cb_play_sfx_loop(sound_effect_id)

        case Opcode.FADE_OUT_SFX:
          self.__cb_fade_out_sfx()

      if self.__want_stop:
        break

      self.__current_instruction += 1
      if self.__current_instruction == len(self.__current_script.instructions):
        desc = self.__current_act.script_map[(self.__current_script.script_id, self.__current_script.script_sub_id)]
        if desc.next_script_letter != self.__current_act.letter:
          self.__current_act = load_act(self.__asset_root, desc.next_script_letter)
        if self.__script_type == ScriptType.SELECTION:
          if self.__selection_prompt is None:
            raise ValueError('missing selection prompt')
          if len(self.__choices) == 0:
            raise ValueError('missing selection choices')
          next_script_sub_id = desc.next_script_sub_id[self.__cb_ask_choices(self.__selection_prompt, self.__choices)]
          if next_script_sub_id < 0:
            raise ValueError('missing valid jump target for choice')
        else:
          next_script_sub_id = desc.next_script_sub_id[0]
        self.__current_script = load_script(self.__asset_root, desc.next_script_letter, desc.next_script_id, next_script_sub_id)

        next_script_type = self.__current_act.script_map[(desc.next_script_id, next_script_sub_id)].script_type
        self.__script_type = next_script_type
        if next_script_type == ScriptType.SELECTION:
          self.__selection_prompt = None
          self.__choices.clear()
        self.__current_instruction = 0

  def stop(self):
    self.__want_stop = True
