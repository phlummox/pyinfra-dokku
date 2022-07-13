
DONE:

- basic dokku install tested
- also letsencrypt plugin

STILL TO DO:

try with Vagrant instead of docker.

use Tox plus tox-gh-actions (<https://github.com/ymyzk/tox-gh-actions>)
to test against multiple Python versions.

translate over the other ansible roles:

- dokku.configure - does some stuff to the
  default website and sets some useful stuff.

- `dokku.apps.vouch_create` - create and configure
  the Vouch app.

- `dokku.apps.clone-and-push` - a task for doing
  a clone-and-push of some dokku app

might want to try testing whether the roles work
using the pyinfra API as well as the pyinfra
CLI.


