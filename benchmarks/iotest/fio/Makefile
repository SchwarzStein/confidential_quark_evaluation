SHELL := /bin/bash
MKFL		:= $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT		:= $(realpath $(patsubst %/,%,$(dir $(MKFL))))
# Variables
IMAGE_NAME 	:= ubuntu
IMAGE_VERSION   := 22.04
IMAGE           := $(IMAGE_NAME):$(IMAGE_VERSION)
SRV_CONTAINER_NAME  ?= fio_benchmark
LOGDIR		    := $(ROOT)/logs
#
# NOTE: quark 		- our confidential compute Quark
# 	ncc-quark 	- Quark with normal, non-CC, VM
# 	emcc-quark 	- Quark with only SW-based memory isolation
# 	...		- ...
RUNTIME 	?= quark# Standart

#
# NOTE: it effects startup time but not performance
#
IGNORE_ATTESTATION ?= 1
SRVARG =

#
#Test arguments
#
ifeq ($(RUNTIME),)
SRVRNT	= runc
else
SRVRNT = $(RUNTIME)
endif
FILE_SIZE   ?= 16m
BLOCK_SIZE  ?= 4k 8k 16k 1m 2m
OPERATION   ?= read write
ITERATIONS  ?= 100
TEST_ARGS   := -e FSIZE=$(FILE_SIZE) -e BSIZES="$(BLOCK_SIZE)" \
	     	-e OPS="$(OPERATION)" -e RUNTIME=$(SRVRNT) \
	     	-e LOOP=$(ITERATIONS)

build:
	docker images | grep $(IMAGE_NAME) || docker pull $(IMAGE)
	DOCKER_BUILDKIT=1 docker build -t $(SRV_CONTAINER_NAME) -f Dockerfile.benchmark .

run-server:
	@if [ -n "$(IGNORE_ATTESTATION)" ]; then          \
		SRVARG="-e Q_AA_NO_ATTEST=y";             \
	else                                              \
      		echo "Provide required arguments"; exit 1;\
	fi;                                               \
	if [ -z "$(RUNTIME)" ]; then 			  \
      		RUNTIMEARG="--runtime=$(RUNTIME)";        \
      		echo "Docker with runtime:$(RUNTIME)";    \
	else						  \
      		RUNTIMEARG="";			          \
      		echo "Docker with runtime:runc";          \
	fi;                                               \
	echo "Starting test container" ;                  \
	docker run -it --name $(SRV_CONTAINER_NAME) \
		-v $(LOGDIR):/home/logs $(TEST_ARGS) \
		--cpus=2 $$RUNTIMEARG $$SRVARG \
		$(SRV_CONTAINER_NAME);           \
	sudo chown -R ${USER}:${USER} $(LOGDIR);
	@echo "Done. Results saved to ./logs: format RUNTIME_ACTION.csv"

clean:
	docker stop $(SRV_CONTAINER_NAME) || true
	docker rm $(SRV_CONTAINER_NAME) || true

purge:
	${MAKE} clean
	docker rmi $(SRV_CONTAINER_NAME) || true

.PHONY: build run-server clean purge
