
import os.path
import sys

from setuptools import find_packages, setup

def get_version():
  """Get version."""

  sys.path.append("pyinfra_dokku")
  import _version # type: ignore
  return _version.__version__

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# list of setup args:
# see <https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#setup-py>

if __name__ == '__main__':
  setup(
    version         =get_version(),
    name            ='pyinfra-dokku',
    url             ='https://github.com/phlummox/pyinfra-dokku',
    description     ='Install & configure Dokku with pyinfra',
    packages        =find_packages(),
    python_requires = '>=3.7',
    install_requires=('pyinfra>=2'),
    extras_require  ={'test': ['coverage',
                               'pytest',
                               'testinfra',
                              ]
                     },
    author          ='phlummox',
    license         ='BSD2',
    license_files   =('LICENSE',),
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    classifiers     =[
        "Development Status :: 3 - Alpha",
    ],
  )
