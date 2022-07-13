#!/usr/bin/env python3

"""
parse list of dokku plugins
"""

def parse_plugins(inp):
  """
  parse output of `dokku plugin:list`, e.g. something like

      00_dokku-standard    0.27.7 enabled    dokku core standard plugin
      20_events            0.27.7 enabled    dokku core events logging plugin
      app-json             0.27.7 enabled    dokku core app-json plugin
      apps                 0.27.7 enabled    dokku core apps plugin
      builder              0.27.7 enabled    dokku core builder plugin

  etc.

  Will take either a string (str) or list of lines.

  Returns a dict, mapping from string (plugin_name) to dicts of (version,
  enabled-status, description).

  """

  try:
    lines = inp.splitlines()
  except AttributeError:
    lines = inp

  lines = [line.strip() for line in lines]
  result = {}
  for line in lines:
    plugin, version, status, desc = line.split(maxsplit=3)
    result[plugin] = dict(version=version,
                          status=status,
                          description=desc)
  return result

