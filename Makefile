
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

IMAGE_NAME=focal-base
IMAGE_VERSION=0.1.0

#####
# targets

default:
	echo pass

print-image-name:
	@echo $(IMAGE_NAME)

print-image-version:
	@echo $(IMAGE_VERSION)

env:
	$(PYTHON3) -m venv env
	.	activate && \
			$(PIP) install --upgrade pip wheel pip-utils

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
#       $(2) = deploy script to run
#
# example of calling:
#
#		$(call RUN_PYINFRA,@vagrant/dokku_ubu2004,./tests/deploy_scripts/install.py)
RUN_PYINFRA = \
	$(PYINFRA) $(PYINFRA_ARGS) \
		--data fqdn=$(DOKKU_FQDN) \
		$(1) $(2)

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
			$(call RUN_PYINFRA,@vagrant/dokku_ubu2004,./tests/deploy_scripts/install.py)

DOCKERFILE=tests/dockerfiles/focal-base-Dockerfile

# quick-and-dirty
# build of base docker image used for tests
docker-build-base:
	docker -D build \
		-t phlummox/$(IMAGE_NAME):$(IMAGE_VERSION) \
		-f $(DOCKERFILE) \
		tests/dockerfiles/

# build docker image used for tests
# with dokku installed
docker-build-dokku: docker-build-base
	set -evx && \
	ctr="$$(docker -D run $(DOCKER_ARGS) --name dokku-ctr -d phlummox/$(IMAGE_NAME):$(IMAGE_VERSION))" && \
	function tearDown { docker stop -t 0 $$ctr; } && \
	trap tearDown EXIT && \
	sleep 4 && \
	$(ACTIVATE) && \
	$(call RUN_PYINFRA,@docker/$$ctr,./tests/deploy_scripts/install.py) && \
	docker -D commit dokku-ctr phlummox/focal-dokku:0.1


# is --privileged needed?
DOCKER_ARGS = --privileged --cap-add SYS_ADMIN \
	-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
	--rm

# run quick-and-dirty docker shell
docker-shell:
	docker -D run $(DOCKER_ARGS) -it --net=host --name dokku-shell-ctr \
		-v $$PWD:/work \
    phlummox/$(IMAGE_NAME):$(IMAGE_VERSION)

# start quick-and-dirty docker server instance
docker-server:
	docker -D run $(DOCKER_ARGS) --name dokku-ctr -it \
		-v $$PWD:/work \
    phlummox/$(IMAGE_NAME):$(IMAGE_VERSION)


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


