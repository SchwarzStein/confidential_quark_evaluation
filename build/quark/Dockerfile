# syntax=docker/dockerfile:1.4
FROM ubuntu:22.04 AS build

ENV DEBIAN_FRONTEND=noninteractive
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV PATH=$CARGO_HOME/bin:$PATH

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libcap-dev \
    git \
    ca-certificates \
    bash \
    pkg-config \
 && rm -rf /var/lib/apt/lists/*

# Install Rustup and the nightly toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
 && rustup toolchain install nightly-2023-12-11-x86_64-unknown-linux-gnu \
 && rustup default nightly-2023-12-11-x86_64-unknown-linux-gnu \
 && rustup component add rust-src \
 && cargo install cargo-xbuild

# Verify installation
RUN rustc --version && cargo --version

WORKDIR /home

COPY <<'EOF' ./build.sh
#!/bin/bash

git clone https://github.com/SchwarzStein/AToughBox.git
cd AToughBox
make release
cp target/release/quark /home/build
cp build/qkernel.bin /home/build
EOF

CMD ["/bin/bash", "/home/build.sh"]

