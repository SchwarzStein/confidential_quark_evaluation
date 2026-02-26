SHELL := /bin/bash
MKFL		:= $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT		:= $(realpath $(patsubst %/,%,$(dir $(MKFL))))
# Variables
IMAGE_NAME 	:= nginx
IMAGE_VERSION   := 1.29.0
IMAGE           := $(IMAGE_NAME)_benchmark
CLT_CONTAINER_NAME  := $(IMAGE_NAME)_client
SRV_CONTAINER_NAME  ?= $(IMAGE_NAME)-benchmark
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
SRV_HOSTNAME := $(SRV_CONTAINER_NAME)
CONNECTIONS  := 200 400 600 800 1000
CONN 	     ?=
THREADS      ?= 10
ARGS 	      = -e SHNAME=$(SRV_HOSTNAME) -e THR=$(THREADS) \
		-e CON=$(CONN) -e RUNTIME=$(SRVRNT)

build:
	docker images | grep $(IMAGE) || \
		DOCKER_BUILDKIT=1 docker build -t $(IMAGE) -f Dockerfile.server .
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
      		RUNTIMEARG="";			          \
      		echo "Docker with runtime:runc";          \
	fi;                                               \
	docker run -d --name $(SRV_CONTAINER_NAME) \
		--cpus=30 $$RUNTIMEARG $$SRVARG \
		--network $(TEST_NETWORK) $(IMAGE)

run-clients:
	@echo "Starting client container"
	docker run -it --network $(TEST_NETWORK) \
		-v $(LOGDIR):/home/logs $(ARGS) \
		--name $(CLT_CONTAINER_NAME) $(CLT_CONTAINER_NAME)

run-test:
	mkdir -p $(LOGDIR)
	@for con in $(CONNECTIONS); do \
		echo ">>> Start test with CONN=$$con";    \
		$(MAKE) run-server || exit 1;             \
		$(MAKE) CONN=$$con run-clients || exit 1; \
		$(MAKE) clean; \
	done
	sudo chown -R ${USER}:${USER} $(LOGDIR)
	@echo "Done. Round results saved to $(LOGDIR): format CONN_RUNTIME_benchmark_results.csv"
	@echo "Final resutls in:$(LOGDIR)/nginx_$(RNTLOG)_benchmark_results.csv"
	@resfile="$(LOGDIR)/nginx_$(RNTLOG)_benchmark_results.csv"; \
	echo "test,${RNTLOG}" > $$resfile; \
	for con in $(CONNECTIONS); do \
		file="$(LOGDIR)/$${con}_$(RUNTIME)_benchmark_results.csv"; \
		getv=$$(awk -F, '/^GET/ {print $$2}' $$file); \
		echo "GET_$${con},$${getv}" >> $$resfile; \
	done

clean:
	docker stop $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true
	docker rm $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true

purge:
	${MAKE} clean
	docker network rm -f $(TEST_NETWORK)
	docker rmi $(CLT_CONTAINER_NAME) || true
	docker rmi $(IMAGE) || true

.PHONY: build run-server run-clients clean purge run-test
