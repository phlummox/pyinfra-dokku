
DONE:

- basic dokku install

STILL TO DO:

finish off goss/infra-style testing of "install dokku"
role.

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


TIDYING:

- no longer a need for requirements.txt etc, remove them from
  repo and makefiles



