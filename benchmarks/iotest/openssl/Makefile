# Variables
IMAGE_NAME=openssl-native-io
CONTAINER_NAME=native-server
PORT=4433
RESULTS_FILE=native_benchmark_results.csv

build:
	docker build -f Dockerfile.native -t $(IMAGE_NAME) .

run-server:
	@echo "Starting Native OpenSSL Server..."
	docker run -d --name $(CONTAINER_NAME) \
		-p $(PORT):$(PORT) $(IMAGE_NAME) \
		s_server -accept $(PORT) -WWW -cert cert.pem -key key.pem

run-clients:
	@echo "Size,Iteration,ConnPerUserSec,RealSec,Throughput_MBs" > $(RESULTS_FILE)
	@for size_name in 1KB 2KB 4KB 8KB 16KB 32KB 64KB 128KB 256KB 512KB 1MB 2MB 4MB 8MB 16MB; do \
		echo ">>> Benchmarking Native Size: $$size_name..."; \
		for i in {1..1000}; do \
			RESULT=$$(openssl s_time -connect localhost:$(PORT) -www /files/$$size_name.bin -time 1 -new 2>&1); \
			CONNS=$$(echo "$$RESULT" | grep "connections in" | awk '{print $$1}' | tr -d '[:space:]'); \
			USER_SEC=$$(echo "$$RESULT" | grep "connections/user sec" | awk '{print $$4}' | tr -d '[:space;]'); \
			REAL_SEC=$$(echo "$$RESULT" | grep "real seconds" | awk '{print $$4}' | tr -d '[:space:]'); \
			BYTES_CONN=$$(echo "$$RESULT" | grep "bytes read per connection" | awk '{print $$4}' | tr -d '[:space:]'); \
			MB_S=$$(echo "scale=4; ($$BYTES_CONN * $$CONNS) / ($$REAL_SEC * 1048576)" | bc); \
			echo "$$size_name,$$i,$$USER_SEC,$$REAL_SEC,$$MB_S" >> $(RESULTS_FILE); \
		done; \
	done
	@echo "Done. Native results saved to $(RESULTS_FILE)"

clean:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

.PHONY: build run-server run-clients clean
