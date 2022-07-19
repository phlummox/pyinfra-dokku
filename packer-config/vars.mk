
# version being built

BOX_VERSION=0.0.1

# packer config file to use
PACKER_FILE=dokku.pkr.hcl

# input box to use
BASE_BOX_NAME=ubuntu2004
BASE_BOX=generic/$(BASE_BOX_NAME)
BASE_BOX_VERSION=4.1.0
UBUNTU_IMG_PATH=virtualbox.box

# name for our built box
BOX_NAME=ubuntu-dokku

SHORT_DESCRIPTION=Dokku installed on Ubuntu 20.04

# markdown fragment
DESCRIPTION=\
$$'Dokku installed on Ubuntu 20.04\ \n\
Built from github repo at https://github.com/phlummox/pyinfra-dokku\ \n'


