
.PHONY: packer-build install_packer \
   clean print_img_path print_box_name

.PRECIOUS: \
	$(BASE_BOX_NAME).json \
	$(UBUNTU_IMG_PATH) \
	$(UBUNTU_IMG_PATH).sha256 \
	$(UBUNTU_IMG_PATH).size

.DELETE_ON_ERROR:

SHELL=bash

include vars.mk

print_img_path:
	@echo $(UBUNTU_IMG_PATH)

print_box_name:
	@echo $(BOX_NAME)

print_box_version:
	@echo $(BOX_VERSION)

print_short_desc:
	@echo '$(SHORT_DESCRIPTION)'

print_desc:
	@printf '%s' $(DESCRIPTION)

# box listing from vagrant cloud
$(BASE_BOX_NAME).json:
	curl -q -L -H "Accept: application/json" "https://vagrantcloud.com/$(BASE_BOX)" > $@

# jq expression for extracting checksum
# from $(BASE_BOX_NAME).json
checksum_extractor = .["versions"] | map(select(.["version"] == "4.1.0")) | .[0]["providers"] | map (select(.["name"] == "virtualbox")) | .[0]["checksum"]
box_url = https://vagrantcloud.com/generic/boxes/$(BASE_BOX_NAME)/versions/$(BASE_BOX_VERSION)/providers/virtualbox.box 

$(UBUNTU_IMG_PATH) \
$(UBUNTU_IMG_PATH).sha256	: $(BASE_BOX_NAME).json
	# extract checksum, download and check
	set -x && \
	checksum=`jq -r '$(checksum_extractor)' $<` && \
	echo "$$checksum $(UBUNTU_IMG_PATH)" > $(UBUNTU_IMG_PATH).sha256 && \
	wget --no-use-server-timestamps -O $(UBUNTU_IMG_PATH) $(box_url) && \
	cat $(UBUNTU_IMG_PATH).sha256 | sha256sum --check --status

$(UBUNTU_IMG_PATH).ovf: $(UBUNTU_IMG_PATH)
	ln -s $< $@

# extract size in bytes of disk
$(UBUNTU_IMG_PATH).size: $(UBUNTU_IMG_PATH)
	tar xf $(UBUNTU_IMG_PATH) --to-stdout box.ovf \
		| grep -o 'ovf:capacity="[^"]\+"' \
		| sed 's/.*=//; s/"//g' \
		> $@



PACKER_VERSION=1.8.2
PACKER_URL=https://releases.hashicorp.com/packer/$(PACKER_VERSION)/packer_$(PACKER_VERSION)_linux_amd64.zip

# installs packer if it's not on path.
# Assumes you have ~/.local/bin, and
# that that's a sensible place to put things

# name used in .hcl file for build, and which therefore ends up in
# artifact names

BUILD_NAME=ubuntu_dokku

install_packer:
	@if (which packer) ; then \
	  echo "packer already installed"; \
	else \
	  dir=`mktemp -d tmp-downloaded-packer-exe-XXXXXXXX`; \
	  set -ex; \
	  (cd $$dir && curl -O -L $(PACKER_URL) ); \
	  unzip -d ~/.local/bin $$dir/packer*zip packer ; \
	  : "done"; \
	fi

VAGRANT_VERSION=2.2.19

install_vagrant:
	@if (dpkg -s vagrant | grep 'Status.*installed') ; then \
	  echo "vagrant already installed"; \
	else \
	  set -ex; \
	  dir=`mktemp -d tmp-downloaded-vagrant-deb-XXXXXXXX`; \
	  curl -L https://releases.hashicorp.com/vagrant/$(VAGRANT_VERSION)/vagrant_$(VAGRANT_VERSION)_x86_64.deb > $$dir/vagrant.deb; \
	  sudo apt install $$PWD/$$dir/vagrant.deb; \
	fi

# to work out the disk size:
# we need to run `qemu-img info /path/to/box.img`,
# and look for a line in the output that says:
#     virtual size: 128G (137438953472 bytes)
# or similar.

packer-build: output/$(BUILD_NAME)_$(BOX_VERSION).box.md5 \
	            output/$(BUILD_NAME)_$(BOX_VERSION).box

#	            output/$(BUILD_NAME)_$(BOX_VERSION).qcow2

#	export DISK_SIZE=`qemu-img info $(UBUNTU_IMG_PATH) | grep '^virtual size' | sed 's/(//g' | awk '{ print $4; }'`; \


output/$(BUILD_NAME)_$(BOX_VERSION).box.md5 \
output/$(BUILD_NAME)_$(BOX_VERSION).box \
output/$(BUILD_NAME)_$(BOX_VERSION).ovf.md5 \
output/$(BUILD_NAME)_$(BOX_VERSION).ovf: \
	                $(UBUNTU_IMG_PATH) \
	                $(UBUNTU_IMG_PATH).sha256 \
	                $(UBUNTU_IMG_PATH).size \
									$(UBUNTU_IMG_PATH).ovf
	@if [ ! -f $(UBUNTU_IMG_PATH) ]; then \
	  printf 'no box.img found at %s!\n' $(UBUNTU_IMG_PATH); \
	  exit 1; \
	fi
	set -x && \
	export PKR_VAR_UBUNTU_IMG_PATH=$(UBUNTU_IMG_PATH).ovf && \
	export PKR_VAR_DISK_SIZE=`cat $(UBUNTU_IMG_PATH).size` && \
	export PKR_VAR_DISK_CHECKSUM=`cat $(UBUNTU_IMG_PATH).sha256 | awk '{ print $$1 }'` && \
	export PKR_VAR_BOX_VERSION=$(BOX_VERSION) && \
	packer validate $(PACKER_FILE) && \
	PACKER_LOG=1 packer build $(PACKER_FILE)

clean:
	-rm -rf \
		$(BASE_BOX_NAME).json \
		$(UBUNTU_IMG_PATH) \
    $(UBUNTU_IMG_PATH).sha256 \
		$(UBUNTU_IMG_PATH).ovf \
		output \
    packer_cache

