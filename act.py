# loaders for files used throughout an act's lifetime

from dataclasses import dataclass
import dataclasses
import string
import os.path
import io
import sys
import struct
import enum

class ScriptType(enum.IntEnum):
  SCENARIO = 0
  SELECTION = 1

@dataclass
class SptDesc:
  script_title: str = ''
  first_line_no: int = 0
  last_line_no: int = 0
  script_letter: str = 'A'
  script_id: int = 0
  script_sub_id: int = 0
  script_type: ScriptType = ScriptType.SCENARIO
  next_script_letter: str = 'A'
  next_script_id: int = 0
  next_script_sub_id: list[int] = dataclasses.field(default_factory=lambda: [0] * 10)

@dataclass
class StringTableEntry:
  text_id: int = 0
  offset_in_txd: int = 0
  length: int = 0

@dataclass
class Act:
  letter: str = 'A'
  script_map: dict[tuple[int, int], SptDesc] = dataclasses.field(default_factory=dict)
  strtab: bytes = b''
  str_info: dict[int, StringTableEntry] = dataclasses.field(default_factory=dict)

def load_act(asset_root: str, letter: str) -> Act:
  if len(letter) != 1 or letter not in string.ascii_uppercase:
    raise ValueError(f'not a script letter: {letter!r}')

  act = Act()
  act.letter = letter

  with open(os.path.join(asset_root, 'data', f'ACT_{letter}.DAT'), 'rb') as f:
    with io.BytesIO(f.read()) as buf:
      n_spt_files = int.from_bytes(buf.read(4), sys.byteorder)
      if len(buf.getbuffer()) != 4 + n_spt_files * 156:
        raise ValueError('bad file size')

      while n_spt_files > 0:
        spt_desc = SptDesc()

        title_buf = buf.read(80)
        title_len = title_buf.find(b'\x00')
        spt_desc.script_title = (title_buf if title_len == -1 else title_buf[:title_len]).decode('utf-8')

        spt_desc.first_line_no, spt_desc.last_line_no = struct.unpack('II', buf.read(8))

        script_letter = chr(ord('A') + int.from_bytes(buf.read(4), sys.byteorder))
        if script_letter not in string.ascii_uppercase:
          raise ValueError(f'not a script letter: {script_letter!r}')
        spt_desc.script_letter = script_letter

        script_id, script_sub_id = struct.unpack('II', buf.read(8))
        spt_desc.script_id, spt_desc.script_sub_id = script_id, script_sub_id

        spt_desc.script_type = ScriptType(int.from_bytes(buf.read(4), sys.byteorder))

        buf.read(4)  # skip unk1

        next_script_letter = chr(ord('A') + int.from_bytes(buf.read(4), sys.byteorder))
        if next_script_letter not in string.ascii_uppercase:
          raise ValueError(f'not a script letter: {next_script_letter!r}')
        spt_desc.next_script_letter = next_script_letter

        spt_desc.next_script_id = int.from_bytes(buf.read(4), sys.byteorder)

        next_script_sub_id = struct.unpack('10i', buf.read(40))
        for i, j in enumerate(next_script_sub_id):
          spt_desc.next_script_sub_id[i] = j

        script_map_key = (script_id, script_sub_id)
        if script_map_key in act.script_map:
          raise ValueError(f'duplicate script: {script_id:04}_{script_sub_id:02}')
        act.script_map[script_map_key] = spt_desc
        n_spt_files -= 1

  with open(os.path.join(asset_root, 'data', f'ACT_{letter}_JA.TXD'), 'rb') as f:
    act.strtab = f.read()

  with open(os.path.join(asset_root, 'data', f'ACT_{letter}_JA.PTR'), 'rb') as f:
    with io.BytesIO(f.read()) as buf:
      if buf.read(4) != b'PTR ':
        raise ValueError('bad file magic')

      n_entries = int.from_bytes(buf.read(4), sys.byteorder)
      if len(buf.getbuffer()) != 16 + n_entries * 12:
        raise ValueError('bad file size')

      buf.read(8)  # skip unk1

      while n_entries > 0:
        text_id, offset_in_txd, length = struct.unpack('III', buf.read(12))
        entry = StringTableEntry()
        entry.text_id = text_id
        entry.offset_in_txd = offset_in_txd
        entry.length = length

        if text_id in act.str_info:
          raise ValueError(f'duplicate text ID: {text_id}')
        act.str_info[text_id] = entry
        n_entries -= 1

  return act
