
## set up dev environment

- clone repo and cd in
- `make env` and `. activate`
- `python3 -m pip install -e ".[test]"`

## key libraries used

- pyinfra, for installing/provisioning, obviously
- pytest-testinfra, for testing whether provisioning worked

## directory structure

important directories are:

- util:

  python utility modules used by deploys. (e.g. parsing
  output of linux commands)

- tests:

  tests intended to be run with pytest.

- tests/vagrantfiles:

  Vagrantfiles used in tests

- tests/dockerfiles:

  Dockerfiles used in tests

## Tests

Run tests with `pytest tests`. The output of commands like `vagrant` and `pyinfra` isn't
shown by default; pass `--log-cli-level=DEBUG` to see it.

Tests that use Docker or Vagrant containers aren't run by default (they
are disabled in `setup.cfg`), since Docker and Vagrant may not be
available on some platforms. To run them, use `pytest -m docker` and
`pytest -m vagrant`, respectively.

The project adds some custom command-line options to `pytest`, run
`pytest --help` to get details. But at the time of writing, they are:

- `--base-docker-image`
- `--dokku-docker-image`
- `--keep-containers`

