SHELL := /bin/bash
# Variables
IMAGE_NAME 	:= redis
IMAGE_VERSION   := 8.0
IMAGE           := $(IMAGE_NAME):$(IMAGE_VERSION)
PORT		:= 6379
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
RESULTS_FILE    := $(SRVRNT)_benchmark_results.csv
SRV_HOSTNAME := $(SRV_CONTAINER_NAME)
CLIENTS      ?= 20
REQUESTS     ?= 100000
ARGS 	      = -e SHNAME=$(SRV_HOSTNAME) -e CLN=$(CLIENTS) \
		-e REQS=$(REQUESTS) -e LOG=$(RESULTS_FILE)  \
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
	if [ -n "$(RUNTIME)" ]; then 			  \
      		RUNTIMEARG="--runtime=$(RUNTIME)";        \
      		echo "Docker with runtime:$(RUNTIME)";    \
	else						  \
      		RUNTIMEARG="";          		  \
      		echo "Docker with runtime:runc";          \
	fi;                                               \
	docker run -d --name $(SRV_CONTAINER_NAME) \
		--cpus=2 $$RUNTIMEARG $$SRVARG \
		--network $(TEST_NETWORK) $(IMAGE)

run-clients:
	@echo "Starting client container"
	mkdir -p ./logs
	touch ./logs/$(RESULTS_FILE)
	docker run -it --network $(TEST_NETWORK) \
		-v ./logs:/home/logs $(ARGS) \
		--name $(CLT_CONTAINER_NAME) $(CLT_CONTAINER_NAME)
	@echo "Done. Results saved to $(RESULTS_FILE)"

clean:
	docker stop $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true
	docker rm $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true
	docker network rm -f $(TEST_NETWORK)

purge:
	${MAKE} clean
	docker rmi $(CLT_CONTAINER_NAME)

.PHONY: build run-server run-clients clean purge
