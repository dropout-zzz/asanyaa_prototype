# preloaded global game resources

from dataclasses import dataclass
from table import load_table, Table
import re
from utils import resolve_path_case_insensitive
from system_messages import SystemMessageTable, load_system_messages

@dataclass
class Foo:
  bmp_tbl: Table
  cv_div: dict[int, list[int]]
  bgm_tbl: Table
  se_tbl: Table
  system_messages: SystemMessageTable
  movie_tbl: Table

def foo_init(asset_root: str) -> Foo:
  tmp = {}

  tmp['bmp_tbl'] = load_table(asset_root, 'bmp')

  with open(resolve_path_case_insensitive(asset_root, 'data', 'cvdiv.txt'), 'r') as f:
    tmp['cv_div'] = {}

    for row in f.read().removesuffix('\n').split('\n'):
      character_id, *n = map(int, re.findall(r'\d+', row))
      if character_id in tmp['cv_div']:
        raise ValueError('duplicate character id')
      tmp['cv_div'][character_id] = n

  tmp['bgm_tbl'] = load_table(asset_root, 'bgm')
  tmp['se_tbl'] = load_table(asset_root, 'se')

  tmp['system_messages'] = load_system_messages(asset_root)

  tmp['movie_tbl'] = load_table(asset_root, 'movie')

  return Foo(**tmp)
