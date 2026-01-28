SHELL := /bin/bash
MKFL		:= $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT		:= $(realpath $(patsubst %/,%,$(dir $(MKFL))))

MEMTESTS := $(ROOT)/benchmarks/memtest
IOTESTS	 := $(ROOT)/benchmarks/iotest
MEMTEST	 := redis memcached
IOTEST	 := fio nginx mariadb openssl

RUNTIME  ?= quark

BUILD := $(ROOT)/build
QUARK := $(BUILD)/quark

.PHONY: build-mem-% build-io-% test-io-% test-mem-% \
	clean-mem-% clean-io-% purge-mem-% purge-io-% \
	install-testbin clean-testbin purge-testbin

install-testbin:
	@echo "Install the test binaries: quark"
	$(MAKE) -C $(QUARK) install

clean-testbin:
	@echo "Remove the test binaries: quark"
	$(MAKE) -C $(QUARK) clean

purge-testbin:
	@echo "Remove the test binaries: quark and build image"
	$(MAKE) -C $(QUARK) purge

build-mem-%:
	$(MAKE) -C $(MEMTESTS)/$* build

build-io-%:
	$(MAKE) -C $(IOTESTS)/$* build

test-mem-%:
	$(MAKE) -C $(MEMTESTS)/$* run-server RUNTIME=$(RUNTIME)
	$(MAKE) -C $(MEMTESTS)/$* run-clients RUNTIME=$(RUNTIME)

test-io-%:
	@if [[ "$*" == "fio" ]]; then \
	$(MAKE) -C $(IOTESTS)/$* run-server RUNTIME=$(RUNTIME); \
	else							\
	$(MAKE) -C $(IOTESTS)/$* run-server RUNTIME=$(RUNTIME); \
	$(MAKE) -C $(IOTESTS)/$* run-clients RUNTIME=$(RUNTIME); \
	fi

clean-mem-%:
	$(MAKE) -C $(MEMTESTS)/$* clean

clean-io-%:
	$(MAKE) -C $(IOTESTS)/$* clean

purge-mem-%:
	$(MAKE) -C $(MEMTESTS)/$* purge

purge-io-%:
	$(MAKE) -C $(IOTESTS)/$* purge
