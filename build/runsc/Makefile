SHELL := /bin/bash
MKFL  := $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT  := $(realpath $(patsubst %/,%,$(dir $(MKFL))))
SRC   := https://github.com/google/gvisor.git
BIN   := $(ROOT)/bin

.PHONY: install

install:
	mkdir -p $(BIN)
	git clone $(SRC)
	{ \
		pushd gvisor; \
		make copy TARGETS=runsc DESTINATION=$(BIN)/; \
		popd; \
		rm -r gvisor; \
	}
