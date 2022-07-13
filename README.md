# pyinfra-dokku

[![build](https://github.com/phlummox/pyinfra-dokku/actions/workflows/build.yml/badge.svg)](https://github.com/phlummox/pyinfra-dokku/actions/workflows/build.yml)

[PyInfra](https://pyinfra.com) package for installing and configuring
[Dokku](https://dokku.com) on a host.

## requirements

- A Python interpreter, >= 3.7.
- pyinfra: can be installed with `pip install pyinfra`

## installation

```
$ python3 -m pip install https://github.com/phlummox/pyinfra-dokku/archive/refs/heads/master.zip
```

## usage

Write an deployment script (called, say, `install_dokku.py`) like the following
(taken from `tests/deploy_scripts/install.py`):

```
"""
install dokku and add the LetsEncrypt plugin.
"""

import pyinfra_dokku.install as di

di.install_dokku()
di.install_letsencrypt_plugin()
```

To run it, you'll need to provide the fully-qualified domain name
(FQDN) of the server that Dokku will be running on, and you'll
need SSH access to that server.
Supposing the FQDN is `example.com`, then the deployment script can then be run
as follows:


```
$ pyinfra --data fqdn=example.com example.com ./install_dokku.py
```

(`--data fqdn=example.com` tells PyInfra what FQDN to use, and the second
`example.com` is the host to SSH into; these needn't necessarily be the same.)


