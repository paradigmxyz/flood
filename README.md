
# RPC Bench

A tool for benchmarking and load testing EVM nodes

`rpc_bench` can measure many different types of workloads
- it separately measure performance of every JSON-RPC method type
- it perform stress tests, spike tests, and soak tests

`rpc_bench` measures a variety of performance metrics including:
1. throughput
2. latency (mean, P50, P90, P95, P99, max)
3. error rate

`rpc_bench` makes it easy to compare the performance of:
- different node clients (e.g. geth vs erigon vs reth)
- different hardware configurations (e.g. local vs cloud vs low memory vs RAID-0)
- different RPC providers (e.g. Alchemy vs Quicknode vs Infura)

`rpc_bench` can generate tables, figures, and reports to make its results interpretable (example report [here])


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

#### run test
```
rpc_bench eth_getBlockByNumber NODE1_NAME=NODE1_URL NODE2_NAME=NODE2_URL --rates 10 100 1000 --duration 30
```

#### orchestrate tests on remote nodes
```
rpc_bench eth_getBlockByNumber NODE1_NAME=NODE1_URL:localhost:8545 NODE2_NAME=NODE2_URL:localhost:8545
```

#### create report
```
rpc_bench report tests/test1_output tests/test2_output
````

## Code Layout
- `rpc_bench/cli`: command line interface
- `rpc_bench/generators`: utilities for generating sequences of rpc calls with parameterized distributions
- `rpc_bench/tests`: implementations of tests
- `rpc_bench/user_io`: utiltiies for parsing user input

