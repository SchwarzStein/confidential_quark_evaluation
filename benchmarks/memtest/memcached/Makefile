SHELL := /bin/bash
# Variables
IMAGE_NAME 	:= memcached
IMAGE_VERSION   := 1.6.38
IMAGE           := $(IMAGE_NAME):$(IMAGE_VERSION)
PORT		:= 11211
CLT_CONTAINER_NAME  := $(IMAGE_NAME)_client
SRV_CONTAINER_NAME  ?= $(IMAGE_NAME)_benchmark
TEST_NETWORK	    := $(IMAGE_NAME)-benchmark-net
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
#Client test arguments
#
ifeq ($(RUNTIME),)
SRVRNT	= runc
else
SRVRNT = $(RUNTIME)
endif
SRV_HOSTNAME := $(SRV_CONTAINER_NAME)
CLIENTS      ?= 100
RANDOM       ?= 1
SET_RATIO    := 1 4 8
ARGS 	      = -e SHNAME=$(SRV_HOSTNAME) -e CLN=$(CLIENTS)  \
		-e RAND=$(RANDOM) -e SETRATIO="$(SET_RATIO)" \
		-e RUNTIME=$(SRVRNT)

build:
	docker images | grep $(IMAGE_NAME) || docker pull $(IMAGE)
	docker network ls | grep $(TEST_NETWORK) || docker network create $(TEST_NETWORK)
	DOCKER_BUILDKIT=1 docker build -t $(CLT_CONTAINER_NAME) -f Dockerfile.client .

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
	docker run -d --name $(SRV_CONTAINER_NAME) \
		--cpus=2 $$RUNTIMEARG $$SRVARG \
		--network $(TEST_NETWORK) $(IMAGE)

run-clients:
	@echo "Starting client container"
	mkdir -p ./logs
	docker run -it --network $(TEST_NETWORK) \
		-v ./logs:/home/logs $(ARGS) \
		--name $(CLT_CONTAINER_NAME) $(CLT_CONTAINER_NAME)
	sudo chown -R ${USER}:${USER} ./logs 
	@echo "Done. Results saved to ./logs: format RUNTIME_SETRATIO.csv"

clean:
	docker stop $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true
	docker rm $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true
	docker network rm -f $(TEST_NETWORK)

purge:
	${MAKE} clean
	docker rmi $(CLT_CONTAINER_NAME)

.PHONY: build run-server run-clients clean purge
