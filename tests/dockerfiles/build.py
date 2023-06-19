#!/usr/bin/env python3

"""
Build docker images

Expected to have following env vars:

IMAGE_NAME
IMAGE_VERSION
GH_IMAGE_ID
REPO_OWNER

And a bunch of org.opencontainers.image metadata
assignments in a file "oc_labels".

1 command-line arg: dockerfile.

Will its parent directory as working directory.

"""

# pylint: disable=missing-class-docstring,missing-function-docstring

import os
import os.path
import subprocess
import sys

from pathlib import Path

args = sys.argv[1:]

if len(args) != 1:
  print("expected 1 arg, dockerfile")
  sys.exit(1)

dockerfile = args[0]
build_dir  = Path(dockerfile).parent

# pylint: disable=invalid-name
try:
  repo_owner = os.environ["REPO_OWNER"]
except KeyError:
  repo_owner = "phlummox"

image_name  = os.environ["IMAGE_NAME"]
version     = os.environ["IMAGE_VERSION"]
gh_image_id = os.environ["GH_IMAGE_ID"]

# org.opencontainers.image metadata
oc_labels = {}

if os.path.isfile("oc_labels"):
  with open("oc_labels", encoding="utf8") as infile:
    for line in infile.readlines():
      k, v = line.strip().split(sep="=", maxsplit=1)
      oc_labels[k] = v
else:
  print("WARNING: no oc_labels file found, image will be missing some labels",
        file=sys.stderr
       )

if oc_labels:
  # override version
  oc_labels["org.opencontainers.image.version"] = version

  # org.label-schema metadata
  ls_labels = { "org.label-schema.schema-version":  "1.0",
                "org.label-schema.build-date":      oc_labels["org.opencontainers.image.created"],
                "org.label-schema.name":            f"{repo_owner}/{image_name}",
                "org.label-schema.description":     oc_labels["org.opencontainers.image.description"],
                "org.label-schema.vcs-url":         oc_labels["org.opencontainers.image.url"],
                "org.label-schema.vcs-ref":         oc_labels["org.opencontainers.image.revision"],
                "org.label-schema.version":         version }
else:
  ls_labels = {}

def verbose_run(cmd, **kwargs):
  print("running: ", cmd, file=sys.stderr)
  sys.stderr.flush()
  sys.stdout.flush()
  # pylint: disable=subprocess-run-check
  subprocess.run(cmd, **kwargs)

# pull existing images if there

cmd = ["docker", "pull", f"{gh_image_id}:{version}"]
verbose_run(cmd, check=False)
cmd = ["docker", "pull", f"{gh_image_id}:latest"]
verbose_run(cmd, check=False)

## builder image
#cmd = f"""docker build --pull -f Dockerfile --target build
#  --cache-from {gh_image_id}:{version}-builder
#  -t {gh_image_id}:{version}-builder .""".split()
#
#verbose_run(cmd, check=True)

# main image
cmd = f"""docker build --pull -f {dockerfile}
  --cache-from {gh_image_id}:{version}-builder
  --cache-from {gh_image_id}:latest
  --cache-from {gh_image_id}:{version}
  -t {gh_image_id}:{version}""".split()

# build up --label args
for k, val in oc_labels.items():
  cmd += ["--label", f"{k}={val}"]

for k, val in ls_labels.items():
  cmd += ["--label", f"{k}={val}"]

cmd += [str(build_dir)]

verbose_run(cmd, check=True)

