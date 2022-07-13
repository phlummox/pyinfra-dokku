"""
test-wide configuration values and fixtures
"""

# pylint: disable=missing-class-docstring,missing-function-docstring,line-too-long

import os

import pytest

# uses env vars.
# alternatively, could use the `pytest_addoption` hook
# to provide new command-line options to `pytest` -- see
# https://stackoverflow.com/questions/54900785/how-to-pass-an-environment-variable-in-command-line-to-pytest-to-test-a-function/55054556
# https://docs.pytest.org/en/7.1.x/example/simple.html#pass-different-values-to-a-test-function-depending-on-command-line-options

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

@pytest.fixture
def base_docker_image(request):
  return request.config.getoption("--base-docker-image")

@pytest.fixture
def docker_base_image():

  if 'DOCKER_BASE_IMAGE' in os.environ:
    return os.environ['DOCKER_BASE_IMAGE']

  return 'phlummox/focal-base:0.1.0'

@pytest.fixture
def docker_dokku_image():

  if 'DOCKER_DOKKU_IMAGE' in os.environ:
    return os.environ['DOCKER_DOKKU_IMAGE']

  return 'phlummox/focal-dokku:0.1.0'


