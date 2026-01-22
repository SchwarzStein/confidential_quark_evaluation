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
    nasm  \
 && rm -rf /var/lib/apt/lists/*

# Install Rustup ...
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y
# ... put rust on Path
ENV PATH="/root/.cargo/bin:${PATH}"

# ... required toolchains
RUN rustup toolchain install nightly-2023-12-11 \
                             nightly-2023-12-31

# ... rust-src for cargo-xbuild
RUN rustup component add rust-src --toolchain nightly-2023-12-11 \
 && rustup component add rust-src --toolchain nightly-2023-12-31

# ... default
RUN rustup default nightly-2023-12-11

# Install cargo-xbuild
RUN cargo install cargo-xbuild

# Verify installation
RUN rustc --version && cargo --version

WORKDIR /home

COPY <<'EOF' ./build.sh
#!/bin/bash

ARCH=$(uname -a)
B=quark_cc_tdx_snp_cca_base_update_safe_arm_intel
git clone -b ${B} https://github.com/SchwarzStein/AToughBox.git
cd AToughBox
if [[ "${ARCH}" == "aarch64" ]]; then
        make release
else
        make cc_x86_release
fi
cp target/release/quark /home/build
cp build/qkernel.bin /home/build
cp vdso/vdso.so /home/build
cp config.json /home/build
if [[ -f td-shim/shim.bin ]]; then
        cp td-shim/shim.bin /home/build
fi
EOF

CMD ["/bin/bash", "/home/build.sh"]

