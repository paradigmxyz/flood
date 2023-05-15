
# RPC Bench

tool for benchmarking RPC calls to a node

a load test is a series of vegeta attacks


## Code Layout
- `rpc_bench/cli`: command line interface
- `rpc_bench/generators`: utilities for generating sequences of rpc calls with parameterized distributions
- `rpc_bench/tests`: implementations of load tests
- `rpc_bench/user_io`: utiltiies for parsing user input

