#!/bin/bash
#
# generate UI code required by the project.
# this should be ran when a .ui file is changed or
#  when ui_*.py does not yet exist.
set -e

if [ $# -gt 0 ]
then
  echo "usage: $0" >&2
  exit 1
fi

# location of `uic' binary on archlinux
PATH="/usr/lib/qt6:${PATH}"
export PATH

dot_ui_names=('title'
              'game_window')

for dot_ui_name in "${dot_ui_names[@]}"
do
  dot_ui_file="${dot_ui_name}.ui"
  dot_ui_py="ui_${dot_ui_name}.py"

  if [ "$dot_ui_py" -nt "$dot_ui_file" \
       -a "$dot_ui_py" -nt "$0" ]
  then
    # up-to-date
    continue
  fi

  (set -x;
   uic -o "$dot_ui_py" -g python "$dot_ui_file")
done

exit 0
