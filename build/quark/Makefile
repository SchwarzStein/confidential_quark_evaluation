SHELL := /bin/bash
MKFL  := $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT  := $(realpath $(patsubst %/,%,$(dir $(MKFL))))
BINDIR:= $(ROOT)/bin
IMAGE := quark-build

ARCH 		:= $(shell uname -m)
X86CPU_TYPE	:= $(shell lscpu | awk -F: '/Vendor ID/ {gsub(/^[ \t]+/, "", $$2); print $$2}')

ifeq ($(ARCH),aarch64)
	CC := Cca
else ifeq ($(X86CPU_TYPE),GenuineIntel)
	CC := TDX
else
	CC := Snp
endif

.PHONY: install clean purge

install:
	mkdir -p $(BINDIR)
	docker images | grep $(IMAGE) || DOCKER_BUILDKIT=1 docker build -t $(IMAGE) .
	docker run --rm -v $(BINDIR):/home/build $(IMAGE)
	@test -f $(BINDIR)/quark -a -f $(BINDIR)/qkernel.bin -a -f $(BINDIR)/vdso.so \
	|| { echo "Quark build failed" ; exit 1; }
	sudo chown -R $(USER):$(USER) $(BINDIR)
	sudo cp $(BINDIR)/{quark,qkernel.bin,vdso.so} /usr/local/bin
	@if [ -f $(BINDIR)/shim.bin ]; then sudo cp $(BINDIR)/shim.bin /usr/local/bin ; fi
	sudo mkdir -p /etc/quark && sudo cp $(BINDIR)/config.json /etc/quark
	@echo "Change /etc/quark/config.json:CCMode to $(CC) for CC or NormalEmu for SW-mem.-isolation"

clean:
	rm -f $(BINDIR)/{quark,qkernel.bin,vdso.so,config.json}

purge:
	$(MAKE) -C $(ROOT) clean
	docker rmi $(IMAGE)
