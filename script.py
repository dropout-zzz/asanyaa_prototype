# script loader and executor

from dataclasses import dataclass
import dataclasses
import string
import os.path
import io
import sys
from act import Act
from act import ScriptType

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

class ScriptExecutor:
  def __init__(self, act: Act, script: Script, instruction_pos: int):
    if act.letter != script.letter or (script.script_id, script.script_sub_id) not in act.script_map:
      raise ValueError('unrelated script and act passed')
    self.__current_act = act
    self.__current_script = script

    if act.script_map[(script.script_id, script.script_sub_id)].script_type == ScriptType.SELECTION and instruction_pos != 0:
      raise ValueError('attempted to resume from middle of a selection script')
    self.__current_instruction = instruction_pos
