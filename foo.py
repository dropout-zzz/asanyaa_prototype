# preloaded global game resources

from dataclasses import dataclass
from table import load_table, Table
import os.path
import re

@dataclass
class Foo:
  bmp_tbl: Table
  cv_div: dict[int, list[int]]
  bgm_tbl: Table

def foo_init(asset_root: str) -> Foo:
  tmp = {}

  tmp['bmp_tbl'] = load_table(asset_root, 'bmp')

  with open(os.path.join(asset_root, 'data', 'cvdiv.txt'), 'r') as f:
    tmp['cv_div'] = {}

    for row in f.read().split('\n'):
      if len(row) == 0:
        continue

      character_id, *n = map(int, re.findall(r'\d+', row))
      if character_id in tmp['cv_div']:
        raise ValueError('duplicate character id')
      tmp['cv_div'][character_id] = n

  tmp['bgm_tbl'] = load_table(asset_root, 'bgm')

  return Foo(**tmp)
