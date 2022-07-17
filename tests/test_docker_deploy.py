"""
test deploy scripts by running in Docker containers.
"""

# pylint: disable=missing-class-docstring,missing-function-docstring

import pytest

from utils import DeploymentTests, PyinfraInvocation, TinfraInvocation


class TestDockerDeploy(DeploymentTests):

  @pytest.mark.docker
  @pytest.mark.container_type("base_docker_image")
  def test_bogus_deploy_script(self, docker_container):
    """
    tests a 'bogus' deploy script that just prints hello world
    (with a base Ubuntu focal image),
    and then verifies that `bash` is installed.

    If this doesn't pass, something's very wrong with our pyinfra or
    docker setup.
    """

    ctr_id = docker_container.id

    pyinfra_args = PyinfraInvocation.make(f"@docker/{ctr_id}")
    testinfra_args = TinfraInvocation.make("docker://" + ctr_id)

    self.bogus_deploy_script(pyinfra_args, testinfra_args)


  @pytest.mark.docker
  @pytest.mark.container_type("base_docker_image")
  def test_dokku_install(self, docker_container):
    """
    try executing the 'dokku install script' at ./tests/deploy_scripts/install.py,
    installing onto a base Focal image.

    Then verify that it probably worked.
    """

    ctr_id          = docker_container.id
    pyinfra_args    = PyinfraInvocation.make(f"@docker/{ctr_id}")
    testinfra_args  = TinfraInvocation.make("docker://" + ctr_id)

    self.dokku_install(pyinfra_args, testinfra_args)


  @pytest.mark.docker
  @pytest.mark.container_type("dokku_docker_image")
  def test_letsencrypt_install(self, docker_container):
    """
    try executing the the 'add letsencrypt plugin' script at
    ./tests/deploy_scripts/install_letsencrypt.py,
    installing onto an image with dokku already installed.

    Then verify that it probably worked.
    """

    ctr_id = docker_container.id
    pyinfra_args    = PyinfraInvocation.make(f"@docker/{ctr_id}")
    testinfra_args  = TinfraInvocation.make("docker://" + ctr_id)

    self.letsencrypt_install(pyinfra_args, testinfra_args)


