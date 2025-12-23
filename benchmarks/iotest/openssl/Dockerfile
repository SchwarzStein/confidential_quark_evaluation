FROM gramineproject/gramine:latest

# Install dependencies
RUN apt-get update && apt-get install -y openssl bash make && rm -rf /var/lib/apt/lists/*

WORKDIR /bench

# 1. Generate benchmark files
RUN mkdir -p /bench/files && \
    for size in 1 4 16 64 256; do \
        dd if=/dev/urandom of=/bench/files/${size}KB.bin bs=1K count=$size; \
    done && \
    for size in 1 4 16; do \
        dd if=/dev/urandom of=/bench/files/${size}MB.bin bs=1M count=$size; \
    done

# 2. Generate TLS certificates
RUN openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem \
    -days 365 -nodes -subj "/CN=localhost"

# 3. Copy external Gramine configuration
COPY openssl.manifest.template /bench/openssl.manifest

# 4. Build and sign the SGX enclave
RUN gramine-manifest openssl.manifest openssl.manifest.sgx && \
    gramine-sgx-gen-private-key && \
    gramine-sgx-sign --manifest openssl.manifest.sgx --output openssl.manifest.sgx --key enclave-key.pem

ENTRYPOINT ["gramine-sgx", "openssl"]

