
# 🌊🌊 flood 🌊🌊

`flood` is a load testing tool for benchmarking EVM nodes over RPC

For each RPC method, `flood` measures the effect of load on metrics such as:
1. throughput
2. latency (mean, P50, P90, P95, P99, max)
3. error rate

`flood` makes it easy to compare the performance of:
- different node clients (e.g. geth vs erigon vs reth)
- different hardware configurations (e.g. local vs cloud vs low memory vs RAID-0)
- different RPC providers (e.g. Alchemy vs Quicknode vs Infura)

`flood` can generate tables, figures, and reports for easy sharing of results (example report [here])


## Installation

#### Prerequisites

Install [`vegeta`](https://github.com/tsenart/vegeta):
- on mac: `brew update && brew install vegeta`
- from source: `go install github.com/tsenart/vegeta@latest`

Install latest [`ctc`](https://github.com/checkthechain/checkthechain):
```
git clone https://github.com/checkthechain/checkthechain
cd checkthechain
pip install -e ./
```

#### Installing `flood`


```
git clone https://github.com/paradigmxyz/flood
cd flood
pip install -e ./
```

## Usage

#### run test
```
flood eth_getBlockByNumber NODE1_NAME=NODE1_URL NODE2_NAME=NODE2_URL --rates 10 100 1000 --duration 30
```

#### orchestrate tests on remote nodes
```
flood eth_getBlockByNumber NODE1_NAME=NODE1_URL:localhost:8545 NODE2_NAME=NODE2_URL:localhost:8545
```

#### create report
```
flood report tests/test1_output tests/test2_output
````

## Code Layout
- `flood/cli`: command line interface
- `flood/generators`: utilities for generating sequences of rpc calls with parameterized distributions
- `flood/tests`: implementations of tests
- `flood/user_io`: utiltiies for parsing user input
