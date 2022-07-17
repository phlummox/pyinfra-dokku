"""
project-wide configuration values and fixtures
"""

# pylint: disable=missing-class-docstring,missing-function-docstring,line-too-long,no-self-use

import logging

from time     import sleep
from types    import SimpleNamespace

import pytest

# pylint: disable=abstract-class-instantiated
from filelock import FileLock

from utils import verbose_run, log_command_output

###
# custom pytest command-line options.
# see https://docs.pytest.org/en/7.1.x/example/simple.html#pass-different-values-to-a-test-function-depending-on-command-line-options
# The tox.ini file is configured so that command-line options after the "--" will
# get passed onto pytest. (See https://tox.wiki/en/latest/example/general.html#interactively-passing-positional-arguments)

def pytest_addoption(parser):

  ###
  # docker images to use

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

  ###
  # whether to tear down vagrant boxes

  parser.addoption(
    "--keep-containers", action='store_const', const=True,
    default=False,
    help="whether to tear down (destroy) vagrant boxes"
  )


###
# fixtures


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




@pytest.fixture
def docker_container(request):
  """
  Spins up a docker container.

  Expects the fixture request to be *marked* with the marker "container_type",
  which should be either "base_docker_image" or
  "dokku_docker_image" (or the name of some other fixture that
  returns or yields a string).

  Yields: an object containing information on the container.

  - Its `.id` attribute is the container ID.
  - Its `.image` attribute is the image it was created from.

  Normally, the container will be stopped after use with the
  `docker stop` command (and, since the container is ephemeral, will also be
  removed); but if the `--keep-containers` was passed to
  pytest, then it won't be.
  """

  marker = request.node.get_closest_marker("container_type")
  logging.info("in docker_container, got marker")
  if marker and marker.args:
    container_type = marker.args[0]
  else:
    logging.warning("no container type specified, using default of base")
    container_type = "base_docker_image"

  image_to_use = request.getfixturevalue(container_type)

  logging.info(f"creating container from image: {image_to_use}")

  # TODO: query: do we need `--privileged`? SYS_ADMIN should be enough.
  # pylint: disable=line-too-long
  cmd  = f"docker -D run --privileged --cap-add SYS_ADMIN -v /sys/fs/cgroup:/sys/fs/cgroup:ro --rm -d {image_to_use}"
  res = verbose_run(["bash", "-c", cmd], capture_output=True, check=True, encoding="utf8")
  ctr_id = res.stdout.strip()

  logging.info(f"got ctr id: {ctr_id}, now sleeping")
  sleep(3.0)

  container = SimpleNamespace(id=ctr_id, image=image_to_use)

  yield container

  if request.config.getoption("--keep-containers"):
    logging.info("--keep-containers passed, not bothering to stop docker")
  else:
    cmd = f"docker -D stop -t 0 {ctr_id}"
    verbose_run(["bash", "-c", cmd], check=True)
    logging.info(f"killed ctr id {ctr_id}")

@pytest.fixture
def vagrant_box(request):
  """
  Spins up a vagrant box from a Vagrantfile. (If the vagrant box is already up,
  has no effect.)

  Expects the fixture request to be *marked* with the marker "vagrantfile",
  which should be the path to a vagrantfile to use.

  Yields: an object containing information on the box.

  - Its `.ssh_config` attribute contains a set of SSH key/value pairs, got from
    running `vagrant ssh_config`. (E.g., 'HostName'='127.0.0.1', etc.)

  - Its `.vagrantfile` (all lowercase) attribute contains the path to the
    vagrantfile used.

  This function assumes each Vagrantfile defines only one box. (The result of
  using a Vagrantfile which defines multiple boxes is undefined.)

  This function creates a lockfile on the Vagrantfile, ensuring only one
  test at a time ever accesses the vagrant box for that file.

  Normally, the vagrant box will be destroyed after use with the
  `vagrant destroy` command; but if the `--keep-containers` was passed to
  pytest, then it won't be.

  The output of the `vagrant up` command is logged at the 'DEBUG' level,
  so pass `--log-cli-level=DEBUG` to pytest if you need to diagnose
  problems with it.
  """

  marker = request.node.get_closest_marker("vagrantfile")
  logging.info("in vagrant_box, got marker")
  if marker and marker.args:
    vagrantfile = marker.args[0]
  else:
    raise Exception("no vagrantfile specified")

  # only one test should access the vagrant box
  # at a time.
  with FileLock(vagrantfile + ".lock") as lock:

    logging.info(f"vagrant, got lockfile for {vagrantfile}: {lock}, {lock.lock_file}")

    logging.info(f"creating vagrant box from file: {vagrantfile}")
    # pylint: disable=line-too-long
    cmd  = f"VAGRANT_VAGRANTFILE={vagrantfile} VAGRANT_LOG=info vagrant up"

    exit_code = log_command_output(cmd, log_prefix="vagrant> ")

    if exit_code != 0:
      raise Exception(f"failure executing {cmd}, exit code was {exit_code}")

    cmd = f"VAGRANT_VAGRANTFILE={vagrantfile} vagrant ssh-config"
    res = verbose_run(["bash", "-c", cmd], check=True, capture_output=True, encoding="utf8")

    ssh_config_lines = [line.strip() for line in res.stdout.splitlines() if line]
    logging.info("got vagrant ssh-config lines: {ssh_config_lines}")

    ssh_config = {}
    for line in ssh_config_lines:
      k, v = line.split()
      ssh_config[k] = v

    box = SimpleNamespace(ssh_config=ssh_config,vagrantfile=vagrantfile)

    sleep(1.0)

    yield box

    if request.config.getoption("--keep-containers"):
      logging.info("--keep-containers passed, not bothering to halt vagrant box")
    else:
      cmd  = f"VAGRANT_VAGRANTFILE={vagrantfile} vagrant halt"
      verbose_run(["bash", "-c", cmd], check=False)
      logging.info("halted vagrant box")
      cmd  = f"VAGRANT_VAGRANTFILE={vagrantfile} vagrant destroy --force"
      verbose_run(["bash", "-c", cmd], check=True)
      logging.info("destroyed vagrant box")


