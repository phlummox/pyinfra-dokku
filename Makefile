
.PHONY: \
	clean							\
	docker-build      \
	docker-shell      \
	docker-test-deploy \
	py-prereqs        \
	pytest            \
	run               \
	vagrant-destroy   \
	vagrant-ssh       \
	vagrant-up        \
	vgarant-test


.DELETE_ON_ERROR:

SHELL=bash

######
# variables available to end-user for
# modification
######

PYTHON3 = python3.8
PIP			= $(PYTHON3) -m pip
PYTEST  = $(PYTHON3) -m pytest
PYINFRA = pyinfra
TOX			= tox

USE_VIRTUALENV=true

ifeq ($(USE_VIRTUALENV), true)
ACTIVATE=. activate
else
ACTIVATE= : "no-op activate"
endif

#####
# targets

env:
	$(PYTHON3) -m venv env
	.	activate && \
			$(PIP) install --upgrade pip wheel pip-utils

#requirements.txt: requirements.in
#	$(ACTIVATE) && \
#		pip-compile $<
#
#py-prereqs: requirements.txt
#	$(ACTIVATE) && \
#		$(PIP) install -r $<

run:
	$(ACTIVATE) && \
	$(PYINFRA) -v inventory.py deploy.py

VAGRANT_VAGRANTFILE=tests/vagrantfiles/ubuntu2004

vagrant-ssh:
	VAGRANT_VAGRANTFILE=$(VAGRANT_VAGRANTFILE) vagrant ssh

pytest:
	$(ACTIVATE) && \
	PYTHONUNBUFFERED=1 $(PYTEST) --verbosity=3 --log-cli-level=INFO --color=yes tests

# requires tox to be on the path
tox:
	PYTHONUNBUFFERED=1 $(TOX) -vvv -epy38

lint:
	$(TOX) -elint


PYINFRA_ARGS = -vv --debug
#PYINFRA_ARGS = -v

# fully-qualified domain name to use when
# configuring dokku
DOKKU_FQDN=localhost.lan

# user-defined function RUN_PYINFRA.
#
# ARGS: $(1) = inventory (host to run on)
#
# example of calling:
#
#		$(call RUN_PYINFRA,@vagrant/dokku_ubu2004)
RUN_PYINFRA = \
	$(PYINFRA) $(PYINFRA_ARGS) \
		--data fqdn=$(DOKKU_FQDN) \
		$(1) \
		./do_install.py

VAGRANT_UP 			= VAGRANT_VAGRANTFILE=$(VAGRANT_VAGRANTFILE) vagrant up
VAGRANT_DESTROY = VAGRANT_VAGRANTFILE=$(VAGRANT_VAGRANTFILE) vagrant destroy --force

vagrant-up:
	$(VAGRANT_UP)

vagrant-destroy:
	$(VAGRANT_DESTROY)

vagrant-test:
	VAGRANT_VAGRANTFILE=$(VAGRANT_VAGRANTFILE) vagrant up
	$(ACTIVATE) && \
		VAGRANT_VAGRANTFILE=$(VAGRANT_VAGRANTFILE) \
			$(call RUN_PYINFRA,@vagrant/dokku_ubu2004)

# docker image to use for testing
DOCKER_IMAGE=phlummox/focal-base:0.1

# build docker image used for tests
docker-build:
	docker -D build \
		-t $(DOCKER_IMAGE) \
		-f tests/dockerfiles/focal-base-Dockerfile \
		tests/dockerfiles/



# is --privileged needed?
DOCKER_ARGS = --privileged --cap-add SYS_ADMIN \
	-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
	--rm

docker-shell:
	docker -D run $(DOCKER_ARGS) -it --net=host --name dokku-shell-ctr \
		-v $$PWD:/work \
    $(DOCKER_IMAGE)

docker-server:
	docker -D run $(DOCKER_ARGS) --name dokku-ctr -it \
		-v $$PWD:/work \
    $(DOCKER_IMAGE)


# not an especially realistic test (the docker container isn't an especially
# good simulacrum of a running Ubuntu VM with systemd as init), but
# quicker to get running than using vagrant.
#
# Does much the same as the "Arrange" and "Act" parts
# of `tests/test_docker_deploy.py`.

#docker-test-deploy:
#	set -evx && \
#	ctr="$$(docker -D run $(DOCKER_ARGS) --name dokku-ctr -d $(DOCKER_IMAGE))" && \
#	function tearDown { docker stop -t 0 $$ctr; } && \
#	trap tearDown EXIT && \
#	sleep 4 && \
#	$(call RUN_PYINFRA,@docker/$$ctr)


clean:
	set -vx && rm -rf build \
		`find -maxdepth 4 -name __pycache__ -o -name '.mypy*' -o -name '*.egg-info' \
		-o -name .tox -o -name .pytest_cache`


