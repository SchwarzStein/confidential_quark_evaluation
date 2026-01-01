SHELL := /bin/bash
MKFL		:= $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT		:= $(realpath $(patsubst %/,%,$(dir $(MKFL))))

MEMTESTS := $(ROOT)/benchmarks/memtest
IOTESTS	 := $(ROOT)/benchmarks/iotest
MEMTEST	 := redis memcached
IOTEST	 := fio nginx mariadb openssl
RUNTIME  ?= quark

.PHONY: $(addprefix build-mem-,$(MEMTEST)) \
	$(addprefix build-io-,$(IOTEST))   \
	$(addprefix test-mem-,$(MEMTEST))  \
	$(addprefix test-io-,$(IOTEST))    \
	$(addprefix clean-mem-,$(MEMTEST)) \
	$(addprefix clean-io-,$(IOTEST))   \
	$(addprefix purge-mem-,$(MEMTEST)) \
	$(addprefix purge-io-,$(IOTEST))

build-mem-%:
	$(MAKE) -C $(MEMTESTS)/$* build

build-io-%:
	$(MAKE) -C $(IOTESTS)/$* build

test-mem-%:
	$(MAKE) -C $(MEMTESTS)/$* run-server RUNTIME=$(RUNTIME)
	$(MAKE) -C $(MEMTESTS)/$* run-client RUNTIME=$(RUNTIME)

test-io-%:
	@if [[ "$*" == "fio" ]]; then \
	$(MAKE) -C $(IOTESTS)/$* run-server RUNTIME=$(RUNTIME); \
	else							\
	$(MAKE) -C $(IOTESTS)/$* run-server RUNTIME=$(RUNTIME); \
	$(MAKE) -C $(IOTESTS)/$* run-client RUNTIME=$(RUNTIME); \
	fi

clean-mem-%:
	$(MAKE) -C $(MEMTESTS)/$* clean

clean-io-%:
	$(MAKE) -C $(IOTESTS)/$* clean

purge-mem-%:
	$(MAKE) -C $(MEMTESTS)/$* purge

purge-io-%:
	$(MAKE) -C $(IOTESTS)/$* purge
