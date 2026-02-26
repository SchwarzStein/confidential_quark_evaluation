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
The Quark configuration file is placed at */etc/quark/*. Quark supports
the following instances, specified in the configuration file *CCMode*-field:

- **None**      – no confidentiality
- **NormalEmu** – nonConfidential, SW-enforced memory separation
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

The results are presentened in the *csv* format. The final result is
places in the *benchmarks/test-type/foo/logs/runtime/foo_benchmark_results.csv*.
Current test runtime versions of Quark are Confidential Quark with TEE support, and
nonConfidential Quark with SW-enforced memory separation. Per default, the benchmarks
run with Quark enabled TEE support, to try *NormalEmu* adjust the test command:
```
make test-type-foo RUNTIME=quark-emcc
```
