SHELL := /bin/bash
MKFL		:= $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT		:= $(realpath $(patsubst %/,%,$(dir $(MKFL))))

MEMTESTS := $(ROOT)/benchmarks/memtest
IOTESTS	 := $(ROOT)/benchmarks/iotest
MEMTEST	 := redis memcached
IOTEST	 := fio nginx mariadb openssl

#quark - runtime with active TEE support
#	- TDX, SEV/SNP, CCA
#quark-emcc - runtime without TEE support,
#	only memory separation
RUNTIME  ?= quark
EFFECTIVE_RUNTIME := $(if $(filter quark-emcc,${RUNTIME}),quark,${RUNTIME})
RNTLOG = $(strip \
$(if $(filter quark,$(RUNTIME)), \
$(if $(filter x86_64,$(ARCH)), \
$(if $(filter GenuineIntel,$(X86CPU_TYPE)),tdx,sevsnp), \
cca), \
emcc))
BUILD := $(ROOT)/build
QUARK := $(BUILD)/quark
QCONFIG := /etc/quark/config.json

ARCH := $(shell uname -m)
X86CPU_TYPE := $(shell lscpu | awk -F: '/Vendor ID/ {gsub(/^[ \t]+/, "", $$2); print $$2}')

.PHONY: build-mem-% build-io-% test-io-% test-mem-% \
	clean-mem-% clean-io-% purge-mem-% purge-io-% \
	install-testbin clean-testbin purge-testbin adjust-runtime

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

test-mem-%: adjust-runtime
	$(MAKE) -C $(MEMTESTS)/$* run-test RUNTIME=$(EFFECTIVE_RUNTIME) RNTLOG=$(RNTLOG)

test-io-%: adjust-runtime
	@if [[ "$*" == "fio" ]]; then \
	$(MAKE) -C $(IOTESTS)/$* run-server RUNTIME=$(EFFECTIVE_RUNTIME) RNTLOG=$(RNTLOG); \
	else							\
	$(MAKE) -C $(IOTESTS)/$* run-test RUNTIME=$(EFFECTIVE_RUNTIME) RNTLOG=$(RNTLOG); \
	fi

clean-mem-%:
	$(MAKE) -C $(MEMTESTS)/$* clean

clean-io-%:
	$(MAKE) -C $(IOTESTS)/$* clean

purge-mem-%:
	$(MAKE) -C $(MEMTESTS)/$* purge

purge-io-%:
	$(MAKE) -C $(IOTESTS)/$* purge

adjust-runtime:
	@echo "Adjust $(QCONFIG) according to runtime:$(RUNTIME)"
	@if [ "$(RUNTIME)" = "quark-emcc" ]; then                                     \
		sudo sed -i 's/"CCMode": *"[^"]*"/"CCMode": "NormalEmu"/' $(QCONFIG); \
		echo "Set CCMode to NormalEmu";					      \
	else									      \
		if [ "$(ARCH)" = "x86_64" ]; then				      \
			if [ "$(X86CPU_TYPE)" = "GenuineIntel" ]; then		      \
				sudo sed -i 's/"CCMode": *"[^"]*"/"CCMode: "TDX"/' $(QCONFIG); \
				echo "Set CCMode to TDX";			      \
			else							      \
				sudo sed -i 's/"CCMode": *"[^"]*"/"CCMode": "SevSnp"/' $(QCONFIG); \
				echo "Set CCMode to SevSnp";			      \
			fi;							      \
		else								      \
			sudo sed -i 's/"CCMode": *"[^"]*"/"CCMode": "Cca"/' $(QCONFIG); \
			echo "Set CCMode to Cca";				      \
		fi;								      \
	fi
