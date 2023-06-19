"""
return version info
"""

VERSION_INFO = (0, 1, 1)

# pylint: disable=redefined-outer-name
def create_valid_version(version_info):
  '''
  Return a version string from version_info.
  '''

  return ".".join([str(c) for c in version_info])

__version__ = create_valid_version(VERSION_INFO)
