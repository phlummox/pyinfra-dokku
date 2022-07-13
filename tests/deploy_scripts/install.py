"""
install dokku and add the LetsEncrypt plugin.
"""

import pyinfra_dokku.install as di

di.install_dokku()
di.install_letsencrypt_plugin()

