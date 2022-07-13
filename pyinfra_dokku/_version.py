"""
return version info
"""

version_info = (0, 1, 0)

# pylint: disable=redefined-outer-name
def create_valid_version(version_info):
  '''
  Return a version string from version_info.
  '''

  return ".".join( [str(c) for c in version_info] )

__version__ = create_valid_version(version_info)
