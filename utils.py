import os.path
import os

def resolve_path_case_insensitive(base: str, *components: str) -> str:
  """join a path from a base directory path and a list of components.
     each component should not contain a path separator.
     this function assumes `base' points to an existing directory.
     on case insensitive file systems, this function directly returns joined path.
     on case senstive file systems, this function returns a case sensitive path,
      resolved using the input arguments while ignoring cases.
     `base' must be case sensitive on case sensitive systems.
     if the path couldnt be found, this function raises a FileNotFoundError exception."""

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
