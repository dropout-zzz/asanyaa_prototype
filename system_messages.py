# loader for messages.txt

from dataclasses import dataclass
import dataclasses
import re

from utils import resolve_path_case_insensitive

@dataclass
class SystemMessageTable:
  strings: dict[str, str] = dataclasses.field(default_factory=dict)

_UNESCAPES: dict[str, str] = {r'\n': '\n', r'\t': '\t'}
_ESCAPES = re.compile('|'.join(map(re.escape, _UNESCAPES.keys())))

def _get_unescaped(m: re.Match) -> str:
  return _UNESCAPES[m.group(0)]

def load_system_messages(asset_root: str) -> SystemMessageTable:
  smt = SystemMessageTable()

  with open(resolve_path_case_insensitive(asset_root,
                                          'data',
                                          'messages.txt'),
            'r',
            encoding='utf-8') as f:
    for line in f.read().removesuffix('\n').split('\n'):
      key, text_escaped = line.split('=', 1)
      if len(key) < 1 or key.isspace():
        raise ValueError('empty message key')
      if key in smt.strings:
        raise ValueError('duplicate message key')
      smt.strings[key] = _ESCAPES.sub(_get_unescaped, text_escaped)

  return smt
