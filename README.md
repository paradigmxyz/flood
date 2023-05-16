
# RPC Bench

tool for benchmarking RPC calls to a node

a load test is a series of vegeta attacks


## Installation

#### Prerequisites

Install [`vegeta`](https://github.com/tsenart/vegeta):
- on mac: `brew update && brew install vegeta`
- from source: `go install github.com/tsenart/vegeta@latest`

Install latest [`ctc`](https://github.com/checkthechain/checkthechain):
```
git clone checkthechain/checkthechain
cd checkthechain
pip install -e ./
```

#### Installing `rpc_bench`


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

