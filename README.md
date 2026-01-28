This repository contains a number of performance tests to evaluate
the Quark Confidential Compute Framework.

## Runtime Installation

To install Quark:
```
make install-testbin
```

A Docker container will be spawned to build the Quark binaries
and place them in the */usr/local/bin* directory. The expected binaries are
*quark*, *qkernel.bin*, *vdso.so*, and in the case of Intel TDX, *shin.bin*.
The Quark configuration file is placed at */etc/quark/*.
To evaluate the implementation with the current HW, adjust the
*CCMode:"..."* field accordingly. The options are:

- **None**      – no confidentiality
- **NormalEmu** – SW-enforced memory isolation
- **TDX**       – Intel TDX support
- **SevSnp**    – AMD Sev/Snp support
- **Cca**       – ARM CCA support

## Benchmarks

This repository includes two sets of benchmarks for the evaluation,
memory-bound applications and IO-bound applications. The list of applications
are categorised as follows:

| Memory Bound | IO Bound |
|--------------|----------|
| Redis        | fio      |
| Memcached    | MariaDB  |
|              | Nginx    |
|              | OpenSSL  |

Performing an evaluation consists of two steps: building and bechmarking.
```
make build-type-foo
```
```
make test-type-foo
```

The placeholder *type* must be replaced with *mem* or *io* as appropriate, while
the placeholder *foo* must be replaced with the name of the application,
all in lowercase, e.g., *redis* for the Redis application benchmark.


