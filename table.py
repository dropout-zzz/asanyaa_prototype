# *.tbl loader

from dataclasses import dataclass
import dataclasses

from utils import resolve_path_case_insensitive

@dataclass
class Table:
  """a loaded .tbl file.

     a .tbl is often used to map some resource ID to
      their file name.

     each row contains a list of item separated by spaces.
     empty lines are allowed.
     comment lines starting with // will be ignored.
     skipped lines and empty lines still counts for row index."""

  # maps row index to items on that row.
  rows: dict[int, list[str]] = dataclasses.field(default_factory=dict)

def load_table(asset_root: str, name: str) -> Table:
  tbl = Table()

  with open(resolve_path_case_insensitive(asset_root,
                                          'data',
                                          f'{name}.tbl'),
            'r',
            encoding='utf-8') as f:
    for i, row in enumerate(f.read().split('\n')):
      comment_start = row.find('//')
      cleaned_row = (row if comment_start < 0 else row[:comment_start]).strip()
      if len(cleaned_row) > 0:
        tbl.rows[i] = cleaned_row.split()

  return tbl
