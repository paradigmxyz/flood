
# <h1 align="center"> 🌊🌊 flood 🌊🌊 </h1>

**`flood` is a load testing tool for benchmarking EVM nodes over RPC**

![](./assets/cover.png)

[![CI status](https://github.com/paradigmxyz/flood/workflows/Pytest/badge.svg)][gh-ci]
[![Telegram Chat][tg-badge]][tg-url]

[gh-ci]: https://github.com/paradigmxyz/flood/actions/workflows/ci.yml
[tg-badge]: https://img.shields.io/endpoint?color=neon&logo=telegram&label=chat&url=https%3A%2F%2Ftg.sumanjay.workers.dev%2Fparadigm%5Fflood
[tg-url]: https://t.me/paradigm_flood

For each RPC method, `flood` measures how load affects metrics such as:
1. throughput
2. latency (mean, P50, P90, P95, P99, max)
3. error rate

`flood` makes it easy to compare the performance of:
- different node clients (e.g. geth vs erigon vs reth)
- different hardware/software configurations (e.g. local vs cloud vs low memory vs RAID-0)
- different RPC providers (e.g. Alchemy vs Quicknode vs Infura)

`flood` can generate tables, figures, and reports for easy sharing of results (example report [here](https://datasets.paradigm.xyz/notebooks/flood/example_report.html))


## Installation

#### Prerequisites

Install [`vegeta`](https://github.com/tsenart/vegeta):
- on mac: `brew update && brew install vegeta`
- on linux: `go install github.com/tsenart/vegeta/v12@v12.8.4`

After installation, make sure `vegeta` is on your `$PATH`. Running `vegeta -h` should output a path. If it does not, you probably have not set up `go` to install items to your `$PATH`. You may need to add something like `export PATH=$PATH:~/go/bin/` to your terminal config file (e.g. `~/.profile`).

`flood` also requires `python >= 3.7`

#### Installing `flood`

```
pip install paradigm-flood
```

Typing `flood help` in your terminal should show help output. If it does not, you probably have not set up `pip` to install items to your `$PATH`. You may need to add something like `export PATH=$PATH:~/.local/bin` to your terminal config file (e.g. `~/.profile`). Alternatively, you can avoid setting up your `$PATH` and just type `python3 -m flood` instead of `flood`.

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
- `flood/generators`: utilities for generating rpc calls with parameterized distributions
- `flood/tests`: implementations of load tests and equality tests
- `flood/user_io`: utiltiies for parsing user io


## Contributing

Contributions are welcome in the form of issues, PR's, and commentary. Check out the contributor guide in [CONTRIBUTING.md](CONTRIBUTING.md).

