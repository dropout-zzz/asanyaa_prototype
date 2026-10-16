# preloaded global game resources

from dataclasses import dataclass
from table import load_table, Table

@dataclass
class Foo:
  bmp_tbl: Table

def foo_init(asset_root: str) -> Foo:
  tmp = {}

  tmp['bmp_tbl'] = load_table(asset_root, 'bmp')

  return Foo(**tmp)
