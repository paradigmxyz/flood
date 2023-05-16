
# RPC Bench

tool for benchmarking RPC calls to a node

a load test is a series of vegeta attacks


## Installation

```
git clone https://github.com/paradigmxyz/rpc_bench
cd rpc_bench
pip install -e ./
```

## Usage

```
rpc_bench eth_getBlockByNumber NODE1_NAME=NODE1_URL NODE2_NAME=NODE2_URL --rates 10 100 1000 --duration 30
```


## Code Layout
- `rpc_bench/cli`: command line interface
- `rpc_bench/generators`: utilities for generating sequences of rpc calls with parameterized distributions
- `rpc_bench/tests`: implementations of load tests
- `rpc_bench/user_io`: utiltiies for parsing user input

