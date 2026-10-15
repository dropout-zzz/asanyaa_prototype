# script loader and executor

from dataclasses import dataclass
import dataclasses
import string
import os.path
import io
import sys

@dataclass
class Instruction:
  opcode: int = 0
  arguments: bytes = b'\x00\x00\x00\x00' * 7

@dataclass
class Script:
  instructions: list[Instruction] = dataclasses.field(default_factory=list)

def load_script(asset_root: str, letter: str, script_id: int, script_sub_id: int) -> Script:
  if len(letter) != 1 or letter not in string.ascii_uppercase:
    raise ValueError(f'not a script letter: {letter!r}')

  script = Script()

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
