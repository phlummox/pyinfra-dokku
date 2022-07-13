"""
test-wide configuration values and fixtures
"""

# pylint: disable=missing-class-docstring,missing-function-docstring,line-too-long

import pytest


# custom pytest command-line options.
# see https://docs.pytest.org/en/7.1.x/example/simple.html#pass-different-values-to-a-test-function-depending-on-command-line-options
# The tox.ini file is configured so that command-line options after the "--" will
# get passed onto pytest. (See https://tox.wiki/en/latest/example/general.html#interactively-passing-positional-arguments)

def pytest_addoption(parser):
  parser.addoption(
    "--base-docker-image", action="store",
    default="phlummox/focal-base:0.1.0",
    help="base docker image to use for tests"
  )
  parser.addoption(
    "--dokku-docker-image", action="store",
    default="phlummox/focal-dokku:0.1.0",
    help="docker image with Dokku installed to use for tests"
  )

@pytest.fixture
def base_docker_image(request):
  """
  return the name of a 'base' docker image on which Dokku
  can be installed.
  """

  return request.config.getoption("--base-docker-image")


@pytest.fixture
def dokku_docker_image(request):
  """
  return the name of a docker image on which Dokku
  is already installed.
  """

  return request.config.getoption("--dokku-docker-image")


