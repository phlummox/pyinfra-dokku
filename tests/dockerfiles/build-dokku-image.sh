#!/usr/bin/env bash

# build a docker images that requires systemd to be running.
# does `docker run` for an incoming image, runs a pyinfra deploy
# script, and commits final image.

# Command-line args: IMAGE_IN IMAGE_OUT
#
# image+label for incoming image to use, and tag to apply
# at end.

if (($# != 2)); then
  echo >2 "bad number args. expected IMAGE_IN, IMAGE_OUT"
  exit 1
fi

image_in="$1"; shift
image_out="$1"; shift

set -euo pipefail
set -x

DOCKER_ARGS="--privileged --cap-add SYS_ADMIN -v /sys/fs/cgroup:/sys/fs/cgroup:ro --rm"
PYINFRA_ARGS="-vv --debug"
DOKKU_FQDN="localhost.lan"

ctr="$(docker -D run ${DOCKER_ARGS} --name dokku-ctr -d ${image_in})"

function tearDown { docker stop -t 0 "$ctr"; }

trap tearDown EXIT

sleep 4

pyinfra $PYINFRA_ARGS --data fqdn="$DOKKU_FQDN" @docker/${ctr} ./tests/deploy_scripts/install.py

docker -D commit dokku-ctr "${image_out}"

