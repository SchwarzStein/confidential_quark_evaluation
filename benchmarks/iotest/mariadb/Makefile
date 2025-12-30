SHELL := /bin/bash
# Variables
IMAGE_NAME 	:= mariadb
IMAGE_VERSION   := 11.3
IMAGE           := $(IMAGE_NAME):$(IMAGE_VERSION)
CLT_CONTAINER_NAME  := $(IMAGE_NAME)_client
SRV_CONTAINER_NAME  := $(IMAGE_NAME)_benchmark
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
THREADS      := 1 4 8 16
WRKLOAD	     := read_only write_only
TABLES	     := 20
TABLE_SIZE   ?= 500000
ARGS 	      = -e SHNAME=$(SRV_HOSTNAME) -e THRDS="$(THREADS)" \
		-e TABS=$(TABLES) -e TBSIZE=$(TABLE_SIZE) \
		-e WRK="${WRKLOAD}"
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
		--cpus=2 $$RUNTIMEARG $$SRVARG \
		$(DBARG) --network $(TEST_NETWORK) \
		$(SRV_CONTAINER_NAME)

run-clients:
	@echo "Starting client container"
	mkdir -p ./logs
	docker run -it --network $(TEST_NETWORK) \
		-v ./logs:/home/logs $(ARGS) \
		--name $(CLT_CONTAINER_NAME) $(CLT_CONTAINER_NAME)
	sudo chown -R ${USER}:${USER} ./logs
	@echo "Done. Results saved to ./logs: format RUNTIME_CLIENTS.csv"

clean:
	docker stop $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true
	docker rm $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME) || true
	docker network rm -f $(TEST_NETWORK)

purge:
	${MAKE} clean
	docker rmi $(SRV_CONTAINER_NAME) $(CLT_CONTAINER_NAME)

.PHONY: build run-server run-clients clean purge
