"""
test deploy functions
"""

# pylint: disable=missing-class-docstring,missing-function-docstring

import logging
import subprocess

from time    import sleep

import pytest
import testinfra

@pytest.fixture
def docker_base_container():

  # pylint: disable=line-too-long
  cmd  = "docker -D run --privileged --cap-add SYS_ADMIN -v /sys/fs/cgroup:/sys/fs/cgroup:ro --rm --name dokku-ctr -d phlummox/focal-base:0.1"
  res = subprocess.run(["bash", "-c", cmd], capture_output=True, check=True, encoding="utf8")
  ctr_id = res.stdout.strip()

  logging.info(f"got ctr id: {ctr_id}, now sleeping")
  sleep(3.0)

  yield ctr_id

  cmd = f"docker -D stop -t 0 {ctr_id}"
  subprocess.run(["bash", "-c", cmd], check=True)
  logging.info(f"killed ctr id {ctr_id}")

def test_dokku_install_with_docker(docker_base_container, caplog):
  caplog.set_level(logging.INFO)
  ctr_id = docker_base_container

  logging.warning(f"ctr_id: {ctr_id}")

  # pylint: disable=line-too-long
  cmd = f"pyinfra -vv --debug --data fqdn=localhost.lan @docker/{ctr_id} ./tests/deploy_scripts/install.py"
  # pylint: disable=consider-using-with
  proc = subprocess.Popen(["script", "-ef", "-c", cmd],
                          bufsize=0,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          )

  while True:
    output = proc.stdout.readline()
    if not output and proc.poll() is not None:
      break
    if output:
      logging.info("pyinfra> " + str(output.strip(), 'utf-8'))

  # return a testinfra connection to the container
  host = testinfra.get_host("docker://" + ctr_id)

  dokku = host.package("dokku")
  assert dokku.is_installed

  package_version = dokku.version

  # output should look like "dokku version SOME_VERSION\n"
  cmd = "dokku version"
  cmd_res = host.run("dokku version")

  assert cmd_res.rc == 0, f"'{cmd}' should succeed"

  assert cmd_res.stdout.startswith('dokku version')
  assert cmd_res.stdout.strip().endswith(package_version)


