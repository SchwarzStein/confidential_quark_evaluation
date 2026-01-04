# syntax=docker/dockerfile:1.6
FROM ubuntu:22.04 AS build

ENV DEBIAN_FRONTEND=noninteractive
ENV GO_VERSION=1.22.2
ENV BAZELISK_VERSION=1.19.0
ENV PATH=/usr/local/go/bin:$PATH

# Install only necessary build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    linux-headers-$(uname -r) \
    build-essential \
    ca-certificates \
    git \
    curl \
    bash \
    make \
    pkg-config \
    gcc \
    g++ \
    clang \
    llvm \
    libelf-dev \
    libbpf-dev \
    libc6-dev-i386 \
 && rm -rf /var/lib/apt/lists/*

RUN curl -Lo /usr/local/bin/bazel \
    https://github.com/bazelbuild/bazelisk/releases/download/v${BAZELISK_VERSION}/bazelisk-linux-amd64 \
    && chmod +x /usr/local/bin/bazel

RUN curl -Lo /tmp/go.tar.gz https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf /tmp/go.tar.gz && \
    rm /tmp/go.tar.gz

ENV PATH=/usr/local/go/bin:$PATH

WORKDIR /src
RUN git clone https://github.com/google/gvisor.git
WORKDIR /src/gvisor

RUN --mount=type=cache,target=/root/.cache/bazel \
    --mount=type=cache,target=/root/.cache/go-build \
    --mount=type=cache,target=/root/.cache/go \
    --mount=type=cache,target=/tmp \
    bazel build //runsc:runsc

FROM ubuntu:22.04

WORKDIR /out

COPY --from=build /src/gvisor/bazel-bin/runsc/runsc ./runsc
