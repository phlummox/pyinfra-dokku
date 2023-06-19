
# cf
# <https://github.com/grantstephens/pyinfra-prometheus/blob/master/pyinfra_prometheus/__init__.py>

"""
install and configure Dokku on an Ubuntu server
"""

from io     import BytesIO
from typing import Any, Dict, Mapping, Tuple

from pyinfra              import config, host, logger
from pyinfra.api          import deploy
from pyinfra.facts.server import LinuxName, LsbRelease
from pyinfra.facts.files  import File
from pyinfra.operations   import apt, python, server
from pyinfra.facts.deb    import DebPackage

from .util.debconf        import parse_debconf
from .util.dokku_plugins  import parse_plugins

##
# globals

DOKKU_APT_REPO  = 'https://packagecloud.io/dokku/dokku'
ROOT_ID_PATH    = '/root/.ssh/id_rsa'

class InstallException(Exception):
  """
  Base exception for installation problems.
  """


def get_expected_debconf_values(fqdn: str) -> Mapping[Tuple[str, str], str]:
  """
  return a dict containing the expected (parsed) values
  from `debconf-show dokku`.

  args:

  - fqdn: the fully qualified domain name of the
    server
  """

  return {
      ('dokku', 'key_file'):      '/root/.ssh/id_rsa.pub',
      ('dokku', 'vhost_enable'):  'true',
      ('dokku', 'skip_key_file'): 'true',
      ('dokku', 'nginx_enable'):  'true',
      ('dokku', 'web_config'):    'false',
      ('dokku', 'hostname'):      fqdn,
    }


def get_dokku_configuration():
  """
  return the result of `debconf-show dokku` as a (lightly parsed)
  dict containing configuration keys and values for dokku.

  e.g. ('dokku','key_file') maps to '/root/.ssh/id_rsa.pub'
  """

  command = 'debconf-show dokku'
  status, stdout, stderr = host.run_shell_command(command=command, sudo=config.SUDO)
  if not status:
    raise InstallException(f"couldn't execute '{command}' on host. stderr = {stderr}")
  return parse_debconf(stdout)


def check_dokku_configuration(fqdn: str):
  """
  check that dokku was installed and configured correctly.
  Checks debconf values and contents of `/home/dokku/VHOST`.

  Raises an InstallException if dokku doesn't appear to be
  correctly configured.

  Args:

  - fqdn: fully-qualified domain name of host.
  """

  debconf_values = get_dokku_configuration()
  if debconf_values != get_expected_debconf_values(fqdn):
    mesg = f"dokku configuration didn't give correct debconf values: {debconf_values}"
    raise InstallException(mesg)

  vhost_file = "/home/dokku/VHOST"

  # get conts bytes of /home/dokku/VHOST, or ""
  # if unavailable
  with BytesIO() as fp:
    try:
      host.get_file(vhost_file, fp)
      conts = fp.getvalue()
    except Exception as ex:
      logger.debug("Wasn't able to get contents of vhost_file: %s", ex)
      conts = b""

  try:
    assert conts.strip() == fqdn.encode("utf8"), \
        f"conts is {str(conts)}, should be {fqdn}"
  except AssertionError as ex:
    logger.error("contents of vhost_file '%s' not as expected: %s", vhost_file, ex)


def get_installed_plugins() -> Dict[str, Any]:
  """
  get a dict of plugin info if dokku is installed,
  or empty dict if not (or if something goes wrong).
  """

  command = 'dokku plugin:list'
  try:
    status, stdout, _stderr = host.run_shell_command(command=command, sudo=config.SUDO)
    assert status
    return parse_plugins(stdout)
  except Exception as ex:
    logger.debug("Wasn't able to get list of dokku plugins: %s", ex)
    return {}

def check_letsencrypt_installed():
  """
  check that letsencrypt was installed okay
  (as reported by `dokku plugin:list`).

  Raises an exception if not.
  """

  installed_plugins = get_installed_plugins()

  assert 'letsencrypt' in installed_plugins, \
    "letsencrypt plugin should be installed"


@deploy("Install Dokku")
def install_dokku():
  """
  Install Dokku on an Ubuntu host.

  prerequisites:

  Needs to be an Ubuntu host. (Bionic and focal okay; not
  sure about others.)

  required "data":

  `host.data.get("fqdn")`

  should return the fully-qualified domain-name to be
  used by Dokku.

  (see <https://dokku.com/docs/configuration/domains/#customizing-hostnames>)

  E.g. a server's fqdn might be "example.io";
  then individual dokku apps will get hosted on subdomains of
  that, like "myapp.example.io"
  """

  # TODO: why isn't config.SUDO working? why is _sudo needed
  # for all ops?
  config.SUDO = True

  assert host.get_fact(LinuxName) == 'Ubuntu'

  # pylint: disable=unexpected-keyword-arg
  apt.packages(
    name='Install required packages',
    packages=[\
      'apt-transport-https',
      'bzip2',
      'ca-certificates',
      'curl',
      'docker.io',
      'git',
      'gnupg',
      'gnupg-agent',
      'lsb-base',
      'lsb-release',
      'openssh-client',
      'openssh-server',
      'openssh-server',
      'software-properties-common',
      'tzdata',
      'wget',
    ],
    update=True,
    _sudo=True,
  )

  # pylint: disable=unexpected-keyword-arg
  apt.key(
    name="Install docker apt key",
    src="https://download.docker.com/linux/ubuntu/gpg",
    _sudo=True,
  )

  lsb_info = host.get_fact(LsbRelease)
  linux_id = lsb_info["id"].lower()
  code_name = lsb_info["codename"]

  # pylint: disable=unexpected-keyword-arg
  apt.repo(
    name='Add the Docker apt repo',
    src=(
        f"deb [arch=amd64] https://download.docker.com/linux/ubuntu {code_name} stable"
    ),
    filename="docker",
    _sudo=True,
  )


  # pylint: disable=unexpected-keyword-arg
  apt.key(
    name="Install Dokku apt key",
    src="https://packagecloud.io/dokku/dokku/gpgkey",
    _sudo=True,
  )

  # pylint: disable=unexpected-keyword-arg
  apt.repo(
    name='Add the Dokku apt repo',
    src=(
        f"deb {DOKKU_APT_REPO}/{linux_id}/ {code_name} main"
    ),
    filename="dokku",
    _sudo=True,
  )

  # do we need sudo perms, since this is one of root's
  # files?
  has_root_id = host.get_fact(File, ROOT_ID_PATH, sudo=True,)

  if not has_root_id:
    server.shell(
      name="create root .ssh key if not exist",
      commands=(
          f"sudo ssh-keygen -t rsa -C root@localhost -q -f {ROOT_ID_PATH} -N ''"
      ),
      _sudo=True,
    )

  fqdn = host.data.get("fqdn")
  assert fqdn

  # See whether dokku has already been configured using
  # using 'debconf-set-selections', and if not, do so.

  debconf_values = get_dokku_configuration()
  logger.info("Got initial Dokku debconf result: %s", debconf_values)

  has_dokku = host.get_fact(DebPackage, "dokku")

  if not has_dokku or debconf_values != get_expected_debconf_values(fqdn):
    dokku_configure_script = f"""
    set -euo pipefail;
    set -x;

    echo "dokku dokku/web_config boolean false"   | debconf-set-selections;
    echo "dokku dokku/vhost_enable boolean true"  | debconf-set-selections;
    echo "dokku dokku/nginx_enable boolean true"  | debconf-set-selections;
    echo "dokku dokku/skip_key_file boolean true" | debconf-set-selections;

    # Use the same SSH key for root and the dokku user
    echo "dokku dokku/key_file string /root/.ssh/id_rsa.pub" | debconf-set-selections;

    # We supply FQDN via variable
    echo "dokku dokku/hostname string {fqdn}" | debconf-set-selections;
  """

    logger.info("NB reconfiguring dokku may take a few minutes")

    server.shell(
      name="configure dokku",
      commands=(
          dokku_configure_script
      ),
      _shell_executable='bash',
      _sudo=True,
    )

    apt.packages(
      name="force-(re)install dokku with provided options",
      packages="dokku",
      force=True,
      update=True,
      _sudo=True,
    )

  python.call(
    name='check Dokku was configured correctly',
    function=lambda: check_dokku_configuration(fqdn),
  )

@deploy("Install Dokku LetsEncrypt plugin")
def install_letsencrypt_plugin():
  """
  Install Dokku LetsEncrypt plugin on a host.

  Prereqs:

  - Dokku must be installed.
  """

  # install 'letsencrypt' plugin if not already installed

  installed_plugins = get_installed_plugins()
  logger.debug("Got installed dokku plugins: %s", installed_plugins)

  if 'letsencrypt' not in installed_plugins:
    # pylint: disable=unexpected-keyword-arg
    server.shell(
      name="install letsencrypt plugin",
      commands=(
          "dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git"
      ),
      _sudo=True,
    )

    # adds a cron job to /var/spool/cron/crontabs/dokku
    # which will call `dokku letsencrypt:auto-renew`
    server.shell(
      name="enable letsencrypt auto-renew",
      commands=(
          "dokku letsencrypt:cron-job --add"
      ),
      _sudo=True,
    )

  python.call(
    name='check letsencrypt got installed',
    function=check_letsencrypt_installed,
  )


