import os.path
import os

def resolve_path_case_insensitive(base: str, *components: str) -> str:
  """assumes `base' points to an existing directory."""

  # fast path
  trivial = os.path.join(base, *components)
  if os.path.exists(trivial):
    return trivial

  tmp = [base]
  for component in components:
    # fast path
    if os.path.exists(os.path.join(*tmp, component)):
      tmp.append(component)
      continue

    # now, try to find in parent
    component_upper = component.upper()
    for dirent in os.listdir(os.path.join(*tmp)):
      if dirent.upper() == component_upper:
        tmp.append(dirent)
        break
    else:
      raise FileNotFoundError(f'non-exist path: {trivial!r}')

  return os.path.join(*tmp)
