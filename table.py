# *.tbl loader

from dataclasses import dataclass
import dataclasses
import os.path

@dataclass
class Table:
  rows: dict[int, list[str]] = dataclasses.field(default_factory=dict)

def load_table(asset_root: str, name: str) -> Table:
  tbl = Table()

  with open(os.path.join(asset_root, 'data', f'{name}.tbl'), 'r', encoding='utf-8') as f:
    for i, row in enumerate(f.read().split('\n')):
      comment_start = row.find('//')
      cleaned_row = (row if comment_start < 0 else row[:comment_start]).strip()
      if len(cleaned_row) > 0:
        tbl.rows[i] = cleaned_row.split()

  return tbl
