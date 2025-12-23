NATIVE_IMAGE=openssl-io
NATIVE_CONTAINER=openssl-native-server
PORT=4433

build:
	docker build -f Dockerfile.native -t $(NATIVE_IMAGE) .

run-server:
	@echo "Starting Native OpenSSL Server..."
	docker run -d --name $(NATIVE_CONTAINER) \
		-p $(PORT):$(PORT) $(NATIVE_IMAGE)

run-client:
	@echo "--- Measuring Native I/O Throughput ---"
	@for size in 1KB 64KB 256KB 1MB 16MB; do \
		echo "\n>>> Testing File Size: $$size"; \
		openssl s_time -connect localhost:$(PORT) -www /files/$$size.bin -time 10 -new; \
	done

clean-native:
	docker stop $(NATIVE_CONTAINER) || true
	docker rm $(NATIVE_CONTAINER) || true

