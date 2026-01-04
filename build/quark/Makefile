SHELL := /bin/bash
MKFL  := $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT  := $(realpath $(patsubst %/,%,$(dir $(MKFL))))
BIN   := $(ROOT)/bin

IMAGE := quark-build

.PHONY: install

install:
	mkdir -p $(BIN)
	docker images | grep $(IMAGE) || DOCKER_BUILDKIT=1 docker build -t $(IMAGE) .
	docker run --rm -v $(BIN):/home/build $(IMAGE)
