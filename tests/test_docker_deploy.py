"""
test deploy functions
"""

# pylint: disable=missing-class-docstring,missing-function-docstring

import logging
import subprocess

from time    import sleep

import pytest
import testinfra

def verbose_run(cmd, **kwargs):
  logging.info(f"running cmd: {cmd}")
  # pylint: disable=subprocess-run-check
  return subprocess.run(cmd, **kwargs)


@pytest.fixture
def docker_container(request):
  """
  expects request to be *marked* with "container_type",
  which should be either "base_docker_image" or
  "dokku_docker_image" (or the name of some other fixture that
  returns or yields a string).

  spins up a docker container of that type, and
  yields the container id.
  """

  marker = request.node.get_closest_marker("container_type")
  logging.warning("in docker_container, got marker")
  if marker and marker.args:
    container_type = marker.args[0]
  else:
    logging.warning("no container type specified, using default of base")
    container_type = "base_docker_image"

  image_to_use = request.getfixturevalue(container_type)

  logging.info(f"creating container from image: {image_to_use}")
  # pylint: disable=line-too-long
  cmd  = f"docker -D run --privileged --cap-add SYS_ADMIN -v /sys/fs/cgroup:/sys/fs/cgroup:ro --rm -d {image_to_use}"
  res = verbose_run(["bash", "-c", cmd], capture_output=True, check=True, encoding="utf8")
  ctr_id = res.stdout.strip()

  logging.info(f"got ctr id: {ctr_id}, now sleeping")
  sleep(3.0)

  yield ctr_id

  cmd = f"docker -D stop -t 0 {ctr_id}"
  verbose_run(["bash", "-c", cmd], check=True)
  logging.info(f"killed ctr id {ctr_id}")



@pytest.fixture
def docker_base_container(base_docker_image):

  logging.info(f"using docker base image: {base_docker_image}")
  # pylint: disable=line-too-long
  cmd  = f"docker -D run --privileged --cap-add SYS_ADMIN -v /sys/fs/cgroup:/sys/fs/cgroup:ro --rm --name dokku-ctr -d {base_docker_image}"
  res = verbose_run(["bash", "-c", cmd], capture_output=True, check=True, encoding="utf8")
  ctr_id = res.stdout.strip()

  logging.info(f"got ctr id: {ctr_id}, now sleeping")
  sleep(3.0)

  yield ctr_id

  cmd = f"docker -D stop -t 0 {ctr_id}"
  verbose_run(["bash", "-c", cmd], check=True)
  logging.info(f"killed ctr id {ctr_id}")


def run_pyinfra(inventory: str, deploy_script, data=None):
  """
  run pyinfra, and stream the output to standard out until it stops.

  args:

  - inventory: something like @docker/SOME_CONTAINER_ID

  - data: string of key/value pairs to be passed to pyinfra as --data,
    e.g.  "fqdn=localhost.lan"

  - deploy script: deploy script to execute.
  """

  if data:
    data = f"--data {data}"
  else:
    data = ""

  # pylint: disable=line-too-long
  cmd = f"pyinfra -vv --debug {data} {inventory} {deploy_script}"
  # pylint: disable=consider-using-with
  logging.info(f"starting Popen for command: {cmd}")


  with subprocess.Popen(["script", "-ef", "-c", cmd],
                          bufsize=0,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
  ) as proc:

    while True:
      output = proc.stdout.readline()
      if not output and proc.poll() is not None:
        break
      if output:
        logging.info("pyinfra> " + str(output.strip(), 'utf-8'))

@pytest.mark.container_type("base_docker_image")
def test_bogus_deploy_script(docker_container, caplog):
  """
  tests a 'bogus' deploy script that just prints hello world
  (with a base Ubuntu focal image),
  and then verifies that `bash` is installed.

  If this doesn't pass, something's very wrong with our pyinfra or
  docker setup.
  """

  caplog.set_level(logging.INFO)
  ctr_id = docker_container
  deploy_script = "./tests/deploy_scripts/bogus.py"
  run_pyinfra(f"@docker/{ctr_id}", deploy_script, "fqdn=localhost.lan")

  # return a testinfra connection to the container
  host = testinfra.get_host("docker://" + ctr_id)

  bash = host.package("bash")
  assert bash.is_installed

@pytest.mark.container_type("base_docker_image")
def test_dokku_install_with_docker(docker_container, caplog):
  """
  try executing the 'dokku install script' at ./tests/deploy_scripts/install.py,
  installing onto a base Focal image.

  Then verify that it probably worked.
  """

  caplog.set_level(logging.INFO)
  ctr_id = docker_container
  deploy_script = "./tests/deploy_scripts/install.py"

  run_pyinfra(f"@docker/{ctr_id}", deploy_script, "fqdn=localhost.lan")

  host = testinfra.get_host("docker://" + ctr_id)

  dokku = host.package("dokku")
  assert dokku.is_installed

  package_version = dokku.version

  # run `dokku version`.
  # output should look like "dokku version SOME_VERSION\n"
  cmd = "dokku version"
  cmd_res = host.run("dokku version")

  assert cmd_res.rc == 0, f"'{cmd}' should succeed"

  assert cmd_res.stdout.startswith('dokku version')
  assert cmd_res.stdout.strip().endswith(package_version)


@pytest.mark.container_type("dokku_docker_image")
def test_letsencrypt_install(docker_container, caplog):
  """
  try executing the the 'add letsencrypt plugin script at
  ./tests/deploy_scripts/install_letsencrypt.py,
  installing onto an image with dokku already installed.

  Then verify that it probably worked.
  """

  caplog.set_level(logging.INFO)
  ctr_id = docker_container
  deploy_script = "./tests/deploy_scripts/install_letsencrypt.py"

  run_pyinfra(f"@docker/{ctr_id}", deploy_script)

  host = testinfra.get_host("docker://" + ctr_id)

  dokku = host.package("dokku")
  assert dokku.is_installed

  # 'letsencrypt' should now appear in the output of
  # `dokku plugin:list`
  cmd = "dokku plugin:list | grep '^\\s\\+letsencrypt.*enabled'"
  cmd_res = host.run(cmd)
  assert cmd_res.rc == 0, f"'{cmd}' should succeed"

  # 'letsencrypt' should also now appear in the dokku 'help'.
  cmd = "dokku help | grep letsencrypt"
  cmd_res = host.run(cmd)
  assert cmd_res.rc == 0, f"'{cmd}' should succeed"

