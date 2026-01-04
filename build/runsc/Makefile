SHELL := /bin/bash
MKFL		:= $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT		:= $(realpath $(patsubst %/,%,$(dir $(MKFL))))
IMAGE_NAME	:= gvisor-build
BIN             := $(ROOT)/bin

.PHONY: install

install:
	mkdir -p $(BIN)
	docker images | grep $(IMAGE_NAME) || \
	DOCKER_BUILDKIT=1 docker build \
	-t $(IMAGE_NAME) $(ROOT)
	docker run --rm -v $(BIN):/out $(IMAGE_NAME)
	docker rmi $(IMAGE_NAME)
