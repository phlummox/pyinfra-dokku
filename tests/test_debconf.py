
"""
test pyinfra_dokku.util.debconf module
"""

# pylint: disable=missing-class-docstring,missing-function-docstring

import pytest

from pyinfra_dokku.util import debconf

class TestDebconf:

  @pytest.fixture
  def sample_input(self):
    return """\
* dokku/key_file: /root/.ssh/id_rsa.pub
* dokku/vhost_enable: true
"""

  @pytest.fixture
  def expected_output(self):
    return {
      ('dokku', 'key_file'):      '/root/.ssh/id_rsa.pub',
      ('dokku', 'vhost_enable'):  'true',
    }

  def test_parse_debconf(self, sample_input, expected_output):
    actual = debconf.parse_debconf(sample_input)
    print(actual)
    assert actual == expected_output


