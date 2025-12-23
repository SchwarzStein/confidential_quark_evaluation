IMAGE_NAME=openssl-gramine-io
CONTAINER_NAME=gramine-server
PORT=4433

.PHONY: build run-server run-client clean

build:
	docker build -t $(IMAGE_NAME) .

run-server:
	@echo "Starting Gramine Server..."
	docker run -d --name $(CONTAINER_NAME) \
		--device /dev/sgx_enclave --device /dev/sgx_provision \
		-p $(PORT):$(PORT) $(IMAGE_NAME) \
		s_server -accept $(PORT) -WWW -cert cert.pem -key key.pem

run-client:
	@echo "--- Measuring I/O Throughput ---"
	@for size in 1KB 64KB 256KB 1MB 16MB; do \
		echo "\n>>> Testing File Size: $$size"; \
		openssl s_time -connect localhost:$(PORT) -www /files/$$size.bin -time 10 -new; \
	done

clean:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

