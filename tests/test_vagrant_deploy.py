"""
test deploy scripts by running in Vagrant boxes.
"""

# pylint: disable=missing-class-docstring,missing-function-docstring,line-too-long,no-self-use

import logging

from os.path  import isfile
from typing   import Any, Mapping, Tuple

import pytest
#import testinfra

from utils import DeploymentTests, PyinfraInvocation, TinfraInvocation

def make_ssh_url(ssh_config: Mapping[str,str]) -> Tuple[str,str]:
  """
  given a dict-like of SSH config options (e.g. 'HostName=127.0.0.1'
  etc.), return a tuple of (ssh_url, ssh_extra_options) that can be
  used with testinfra.

  The ssh_extra_options is a string of the form "-o key1=val1 -o
  key2=val2" etc.
  """

  ssh_config = dict(ssh_config)

  # pylint: disable=multiple-statements

  user = ssh_config['User'];      del ssh_config['User']
  host = ssh_config['HostName'];  del ssh_config['HostName']
  port = ssh_config['Port'];      del ssh_config['Port']
  del ssh_config['Host']

  ssh_url = f"ssh://{user}@{host}:{port}"

  ssh_extra_args : Any = []

  for k, v in ssh_config.items():
    ssh_extra_args.append("-o " + k + "=" + v)

  ssh_extra_args = " ".join(ssh_extra_args)

  return (ssh_url, ssh_extra_args)

class TestVagrantDeploy(DeploymentTests):

  @pytest.mark.vagrant
  @pytest.mark.vagrantfile("tests/vagrantfiles/ubuntu2004")
  def test_bogus_deploy_script(self, vagrant_box):
    """
    tests a 'bogus' deploy script that just prints hello world
    and then verifies that `bash` is installed.

    If this doesn't pass, something's very wrong with our pyinfra or
    vagrant setup.
    """

    ssh_config    = vagrant_box.ssh_config
    vagrantfile   = vagrant_box.vagrantfile
    vagrant_host  = ssh_config["Host"]

    if not isfile(vagrantfile):
      raise Exception(
        f"error: can't run vagrant with non-existent vagrantfile {vagrantfile}"
      )

    logging.info(f"got ssh config: {ssh_config}")

    pyinfra_extra_env = dict(
      VAGRANT_VAGRANTFILE=vagrantfile
    )

    pyinfra_kwargs = dict(
      ssh_known_hosts_file="/dev/null",
      ssh_strict_host_key_checking="no",
    )

    ssh_url, ssh_extra_args = make_ssh_url(ssh_config)

    pyinfra_args = PyinfraInvocation.make(f"@vagrant/{vagrant_host}",
                                          pyinfra_extra_env,
                                          **pyinfra_kwargs,
    )

    testinfra_args = TinfraInvocation.make(ssh_url,
                                              ssh_extra_args=ssh_extra_args)

    self.bogus_deploy_script(pyinfra_args,
                             testinfra_args,
    )


  @pytest.mark.vagrant
  @pytest.mark.vagrantfile("tests/vagrantfiles/ubuntu2004")
  def test_dokku_install(self, vagrant_box):
    """
    try executing the 'dokku install script' at ./tests/deploy_scripts/install.py,
    installing onto a base Focal image.

    Then verify that it probably worked.
    """

    ssh_config    = vagrant_box.ssh_config
    vagrantfile   = vagrant_box.vagrantfile
    vagrant_host  = ssh_config["Host"]

    if not isfile(vagrantfile):
      raise Exception(
        f"error: can't run vagrant with non-existent vagrantfile {vagrantfile}"
      )

    logging.info(f"got ssh config: {ssh_config}")

    pyinfra_extra_env = dict(
      VAGRANT_VAGRANTFILE=vagrantfile
    )

    pyinfra_kwargs = dict(
      ssh_known_hosts_file="/dev/null",
      ssh_strict_host_key_checking="no",
    )

    ssh_url, ssh_extra_args = make_ssh_url(ssh_config)

    pyinfra_args = PyinfraInvocation.make(f"@vagrant/{vagrant_host}",
                                          pyinfra_extra_env,
                                          **pyinfra_kwargs,
    )

    testinfra_args = TinfraInvocation.make(ssh_url,
                                              ssh_extra_args=ssh_extra_args)

    self.dokku_install(pyinfra_args,
                       testinfra_args,
    )



