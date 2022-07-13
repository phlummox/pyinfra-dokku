
## set up dev environment

- clone repo and cd in
- `make env` and `. activate`
- `make py-prereqs`
- `python3 -m pip install -e ".[test]"`

## key libraries used

- pyinfra, for installing/provisioning, obviously
- testinfra, for testing whether provisioning worked

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

