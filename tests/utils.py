
"""
utility functions used in tests

"""

# pylint: disable=missing-class-docstring,missing-function-docstring,line-too-long,no-self-use

import logging
import shlex
import subprocess

from os           import environ
from types        import MappingProxyType
from typing       import Any, List, Mapping, NamedTuple, Optional, Sequence, Union

import testinfra


class PyinfraInvocation(NamedTuple):

  """
  Wraps up arguments to be used for running `pyinfra`.

  attributes are:

  - host: specify the host to connect to (e.g. '@docker/SOME_CTR_ID')
  - extra_env: (optional) environment variables to set for the subprocess
  - data_dict: values that get passed to pyinfra on the command-line
    as --data options, e.g. `--data ssh_known_hosts_file=/dev/null`

  Construct new PyinfraInvocation objects with the `make`
  class method.

  """

  host: str
  extra_env: Optional[Mapping[str,str]]
  data_dict: Mapping[str,str]

  @classmethod
  def make(cls,
          host: str,
          extra_env: Optional[Mapping[str,str]]=None,
          **kwargs
  ):
    """
    Construct a new PyinfraInvocation object.
    """

    self = cls(host=host,
               extra_env=extra_env,
               data_dict=kwargs
    )
    return self


class TinfraInvocation(NamedTuple):

  """
  Wraps up arguments to be used for invoking `testinfra`.

  attributes are:

  - target_url: URL specifying the host to connect to (e.g. 'docker://SOME_CTR_ID')
  - kwargs: keyword args that get passed to `testinfra.get_host`.

  Construct new TinfraInvocation objects with the `make`
  class method.

  """

  target_url: str
  kwargs: Optional[Mapping[str,str]]

  @classmethod
  def make(cls,
          target_url: str,
          **kwargs
  ):
    """
    Construct a new TinfraInvocation object.
    """

    self = cls(target_url=target_url,
               kwargs=kwargs
    )
    return self


def verbose_run(cmd : List[str], **kwargs):
  "utility function: verbose wrapper around subprocess.run"

  logging.info(f"running cmd: {cmd}")
  # pylint: disable=subprocess-run-check
  return subprocess.run(cmd, **kwargs)


def log_command_output(cmd : Union[str,Sequence[str]],
                      env=MappingProxyType({}),
                      log_prefix : str = "> "
) -> int:
  """
  run a command using subprocess.Popen and `bash -c`;
  merge the commands stdout and stderr, and log them at the DEBUG
  level.

  args:

  - cmd. Command to run, passed to `Popen`. If it's a string, it'll
    get turned into ['bash', '-c', cmd].
  - env. Extra environment variables to set. These are
    added to os.environ and passed to `Popen`.
  - log_prefix. A string - log messages get prefixed with this.

  returns the exit code.
  """

  popen_env = dict(environ)
  for k, v in env.items():
    popen_env[k] = v

  if isinstance(cmd, str):
    cmd_ = ["bash", "-c", cmd]
  else:
    cmd_ = cmd # type: ignore


  with subprocess.Popen(cmd_,
                        bufsize=0,
                        env=popen_env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
  ) as proc:

    while True:
      output = proc.stdout.readline() # type: ignore
      if not output and proc.poll() is not None:
        break
      if output:
        logging.debug(log_prefix + str(output.strip(), 'utf-8'))

    exit_code = proc.returncode

  return exit_code


def _run_pyinfra(inventory: str, deploy_script : str, env=MappingProxyType({}), **kwargs):
  """
  run pyinfra, and stream the output to standard out until it stops.

  args:

  - inventory: something like @docker/SOME_CONTAINER_ID

  - deploy script: deploy script to execute.

  - env: dict of extra env vars to set in subprocess (i.e. to be added to os.environ)

  - keyword args: Supply any string-value keyword arguments
    you like.

    These will each get passed to pyinfra using the --data option,
    e.g.  "--data fqdn=localhost.lan"

  The output of the `pyinfra` command is logged at the 'DEBUG' level,
  so pass `--log-cli-level=DEBUG` to pytest if you need to diagnose
  problems with it.

  Throws an exception if `pyinfra` didn't give successful exit code.
  """

  # --data options to pass to pyinfra
  data_options : Any = []

  for k, v in kwargs.items():
    data_options.append( "--data " + k + "=" + v )

  data_options = " ".join(data_options)

  # pylint: disable=line-too-long
  cmd = f"pyinfra -vv --debug {data_options} {inventory} {deploy_script}"
  cmd_ = shlex.split(cmd)

  logging.info(f"starting Popen for command: {cmd} with extra env {env}")

  exit_code = log_command_output(cmd_, env=env, log_prefix="pyinfra> ")

  if exit_code != 0:
    raise Exception(f"failure executing {cmd}, exit code was {exit_code}")



class DeploymentTests:

  """
  Container-agnostic portions of our deployment tests - can be run
  on either Docker or Vagrant containers.

  Each method here is intended to be called from test methods
  in a subclass of DeploymentTests.

  e.g. see TestDockerDeploy.test_dokku_install in `test_docker_deploy.py`
  for an example.

  """

  def bogus_deploy_script(self,
                          pyinfra_args : PyinfraInvocation,
                          testinfra_args : TinfraInvocation,
  ):
    """
    tests a 'bogus' deploy script that just prints hello world
    (with a base Ubuntu focal container), and then verifies that `bash` is
    installed.

    If this doesn't pass, something's very wrong with our pyinfra or
    docker/vagrant setup.

    args:

    - pyinfra_args. Args to invoke `pyinfra` with.
    - testinfra_args. Args to invoke pytest-testinfra's
      `get_host` method with.

    """

    deploy_script = "./tests/deploy_scripts/bogus.py"

    # "Act"

    if pyinfra_args.extra_env:
      pyinfra_extra_env = pyinfra_args.extra_env
    else:
      pyinfra_extra_env = {}

    _run_pyinfra(pyinfra_args.host,
                 deploy_script,
                 pyinfra_extra_env,
                 **pyinfra_args.data_dict
    )

    # "Assert"
    if testinfra_args.kwargs:
      host = testinfra.get_host(testinfra_args.target_url,
                                **testinfra_args.kwargs)
    else:
      host = testinfra.get_host(testinfra_args.target_url)

    bash = host.package("bash")
    assert bash.is_installed


  def dokku_install(self,
                    pyinfra_args : PyinfraInvocation,
                    testinfra_args : TinfraInvocation,
  ):
    """
    Try executing the 'dokku install script' at ./tests/deploy_scripts/install.py,
    installing it onto the pyinfra inventory host specified by `pyinfra_target_host`.

    Then verify that it probably worked.

    args:

    - pyinfra_args. Args to invoke `pyinfra` with.
    - testinfra_args. Args to invoke pytest-testinfra's
      `get_host` method with.

    """

    # "Act"

    deploy_script = "./tests/deploy_scripts/install.py"

    if pyinfra_args.extra_env:
      pyinfra_extra_env = dict(pyinfra_args.extra_env)
    else:
      pyinfra_extra_env = {}

    if pyinfra_args.data_dict:
      pyinfra_data = dict(pyinfra_args.data_dict)
    else:
      pyinfra_data = {}

    pyinfra_data["fqdn"] = "localhost.lan"

    _run_pyinfra(pyinfra_args.host,
                 deploy_script,
                 pyinfra_extra_env,
                 **pyinfra_data
    )


    # "Assert" - check properties of host using testinfra.
    if testinfra_args.kwargs:
      host = testinfra.get_host(testinfra_args.target_url,
                                **testinfra_args.kwargs)
    else:
      host = testinfra.get_host(testinfra_args.target_url)

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


  def letsencrypt_install(self,
                          pyinfra_args : PyinfraInvocation,
                          testinfra_args : TinfraInvocation,
  ):
    """
    Try executing the the 'add letsencrypt plugin' script at
    `./tests/deploy_scripts/install_letsencrypt.py`,
    installing onto a container with dokku already installed.

    Then verify that it probably worked.

    args:

    - pyinfra_target_host. A pyinfra inventory host. e.g. "@docker/SOME_CTR_ID".
    - testinfra_host_url. A url for the same host, usable by pytest-testinfra's
      `get_host` method. e.g. "docker://SOME_CTRID".
    """

    # "Act"

    deploy_script = "./tests/deploy_scripts/install_letsencrypt.py"

    if pyinfra_args.extra_env:
      pyinfra_extra_env = pyinfra_args.extra_env
    else:
      pyinfra_extra_env = {}

    if pyinfra_args.data_dict:
      pyinfra_data = dict(pyinfra_args.data_dict)
    else:
      pyinfra_data = {}

    _run_pyinfra(pyinfra_args.host,
                 deploy_script,
                 pyinfra_extra_env,
                 **pyinfra_data
    )

    # "Assert" - check properties of host using testinfra.
    if testinfra_args.kwargs:
      host = testinfra.get_host(testinfra_args.target_url,
                                **testinfra_args.kwargs)
    else:
      host = testinfra.get_host(testinfra_args.target_url)

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


