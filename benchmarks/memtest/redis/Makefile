SHELL := /bin/bash
MKFL		:= $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT		:= $(realpath $(patsubst %/,%,$(dir $(MKFL))))
# Variables
IMAGE_NAME 	:= redis
IMAGE_VERSION   := 8.0
IMAGE           := $(IMAGE_NAME):$(IMAGE_VERSION)
PORT		:= 6379
CLT_CONTAINER_NAME  := $(IMAGE_NAME)_client
SRV_CONTAINER_NAME  ?= $(IMAGE_NAME)_benchmark
TEST_NETWORK	    := $(IMAGE_NAME)-benchmark-net
LOGDIR		    := $(ROOT)/logs/${RNTLOG}
#
# NOTE: quark 		- our confidential compute Quark
# 	quark-emcc 	- Quark with only SW-based memory isolation
RUNTIME 	?= quark# Standart
RNTLOG		?= emcc
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
RESULTS_FILE  = K$(DATA_SIZE)_$(SRVRNT)_benchmark_results.csv
SRV_HOSTNAME := $(SRV_CONTAINER_NAME)
CLIENTS      ?= 100
REQUESTS     ?= 100000
DATA_SIZE_LIST := 4096 8192 12288 16384 32768 65536
DATA_SIZE     ?=
ARGS 	      = -e SHNAME=$(SRV_HOSTNAME) -e CLN=$(CLIENTS) \
		-e REQS=$(REQUESTS) -e LOG=$(RESULTS_FILE)  \
		-e RUNTIME=$(SRVRNT) -e DSIZE=$(DATA_SIZE)

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
		--cpus=30 $$RUNTIMEARG $$SRVARG \
		--network $(TEST_NETWORK) $(IMAGE)

run-clients:
	@echo "Starting client container"
	touch $(LOGDIR)/$(RESULTS_FILE)
	docker run -it --network $(TEST_NETWORK) \
		-v $(LOGDIR):/home/logs $(ARGS) \
		--name $(CLT_CONTAINER_NAME) $(CLT_CONTAINER_NAME)

run-test:
	mkdir -p $(LOGDIR)
	@for ds in $(DATA_SIZE_LIST); do \
		echo ">>> Start test with DATA_SIZE=$$ds";    \
		$(MAKE) run-server || exit 1;                 \
		$(MAKE) DATA_SIZE=$$ds run-clients || exit 1; \
		$(MAKE) clean; \
	done
	sudo chown -R ${USER}:${USER} $(LOGDIR)
	@echo "Done. Round results saved to $(LOGDIR): format KDATA_SIZE_RUNTIME_benchmark_results.csv"
	@echo "Final resutls in:$(LOGDIR)/redis_$(RNTLOG)_benchmark_results.csv"
	@resfile="$(LOGDIR)/redis_$(RNTLOG)_benchmark_results.csv"; \
	echo "test,${RNTLOG}" > $$resfile; \
	for ds in $(DATA_SIZE_LIST); do \
		kb=$$(($$ds / 1024)); \
		file="$(LOGDIR)/K$${ds}_$(RUNTIME)_benchmark_results.csv"; \
		getv=$$(awk -F, '/^GET/ {print $$2}' $$file); \
		setv=$$(awk -F, '/^SET/ {print $$2}' $$file); \
		echo "GET_$${kb}K,$${getv}" >> $$resfile; \
		echo "SET_$${kb}K,$${setv}" >> $$resfile; \
	done

clean:
	docker stop $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true
	docker rm $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true

purge:
	${MAKE} clean
	docker network rm -f $(TEST_NETWORK)
	docker rmi $(CLT_CONTAINER_NAME) || true

.PHONY: build run-server run-clients clean purge run-test
