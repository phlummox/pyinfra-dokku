#!/usr/bin/env python3

"""
parse debconf format
"""

from typing import List, Mapping, Sequence, Tuple, Union, cast

def parse_debconf(inp: Union[str, Sequence[str]]) -> Mapping[Tuple[str, str], str]:
  """
  parse output of `debconf-show`, e.g. something like

    * dokku/key_file: /root/.ssh/id_rsa.pub
    * dokku/vhost_enable: true

  etc.

  Will take either a string (str) or list of lines.

  Returns a dict of (package, varname) to (value) mappings.
  """

  try:
    lines = cast(str, inp).splitlines()
  except AttributeError:
    lines = cast(List[str], inp)

  lines = [line.strip('* ') for line in lines]
  result = {}
  for line in lines:
    pkg, rest = line.split("/", 1)
    var, val  = rest.split(": ", 1)
    result[(pkg,var)] = val
  return result


