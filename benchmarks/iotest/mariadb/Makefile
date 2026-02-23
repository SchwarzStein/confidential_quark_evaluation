SHELL := /bin/bash
MKFL		:= $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT		:= $(realpath $(patsubst %/,%,$(dir $(MKFL))))
# Variables
IMAGE_NAME 	:= mariadb
IMAGE_VERSION   := 11.3
IMAGE           := $(IMAGE_NAME):$(IMAGE_VERSION)
CLT_CONTAINER_NAME  := $(IMAGE_NAME)_client
SRV_CONTAINER_NAME  := $(IMAGE_NAME)_benchmark
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
DBROOTARG = -e MYSQL_ROOT_PASSWORD=root
DBUSERARG = -e MYSQL_DATABASE=btest \
	     -e MYSQL_USER=user -e MYSQL_PASSWORD=pass
DBARG     = $(DBROOTARG) $(DBUSERARG) \
	    -v mariadb-data:/var/lib/mysq

#
#Client test arguments
#
ifeq ($(RUNTIME),)
SRVRNT	= runc
else
SRVRNT = $(RUNTIME)
endif
SRV_HOSTNAME := $(SRV_CONTAINER_NAME)
THREADS      := 4 8 16 32
THRD 	     ?=
WRKLOAD	     := read_only write_only
TABLES	     := 20
TABLE_SIZE   ?= 100000
ARGS 	      = -e SHNAME=$(SRV_HOSTNAME) -e THRDS=$(THRD) \
		-e TABS=$(TABLES) -e TBSIZE=$(TABLE_SIZE) \
		-e WRK="${WRKLOAD}" \
		-e RUNTIME=$(SRVRNT) $(DBUSERARG)

build:
	docker images | grep $(IMAGE_NAME) || docker pull $(IMAGE)
	docker network ls | grep $(TEST_NETWORK) || docker network create $(TEST_NETWORK)
	DOCKER_BUILDKIT=1 docker build -t $(SRV_CONTAINER_NAME) -f Dockerfile.server .
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
		$(DBARG) --network $(TEST_NETWORK) \
		$(SRV_CONTAINER_NAME)

run-clients:
	@echo "Starting client container"
	docker run -it --network $(TEST_NETWORK) \
		-v $(LOGDIR):/home/logs $(ARGS) \
		--name $(CLT_CONTAINER_NAME) $(CLT_CONTAINER_NAME)

run-test:
	mkdir -p $(LOGDIR)
	@for t in $(THREADS); do \
		echo ">>> Start test with THREADS=$$t"; \
		$(MAKE) run-server || exit 1;           \
		$(MAKE) THRD=$$t run-clients || exit 1; \
		$(MAKE) clean; \
	done
	sudo chown -R ${USER}:${USER} $(LOGDIR)
	@echo "Done. Round results saved to $(LOGDIR): format THRD_RUNTIME_benchmark_results.csv"
	@echo "Final resutls in:$(LOGDIR)/mariadb_$(RNTLOG)_benchmark_results.csv"
	@resfile="$(LOGDIR)/mariadb_$(RNTLOG)_benchmark_results.csv"; \
	echo "test,${RNTLOG}" > $$resfile; \
	for t in $(THREADS); do \
		file="$(LOGDIR)/$${t}_$(RUNTIME)_benchmark_results.csv"; \
		rv=$$(awk -F, '/^read_only/ {print $$2}' $$file); \
		wv=$$(awk -F, '/^write_only/ {print $$2}' $$file); \
		echo "Read_$${t},$${rv}" >> $$resfile; \
		echo "Write_$${t},$${wv}" >> $$resfile; \
	done

clean:
	docker stop $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true
	docker rm $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true

purge:
	${MAKE} clean
	docker network rm -f $(TEST_NETWORK)
	docker rmi $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true

.PHONY: build run-server run-clients clean purge run-test
