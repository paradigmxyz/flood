from __future__ import annotations

import typing

import toolcli

import rpc_bench

help_message = """Benchmark a set of node endpoints

Basic node syntax is [metavar]url[/metavar] or [metavar]name=url[/metavar]
- The [metavar]name[/metavar] of each node will be output in summary reports

[metavar]rpc_bench[/metavar] can also be invoked on remote machines
- Use node syntax [metavar]user@remote:node_url[/metavar] or [metavar]name=user@remote:node_url[/metavar]
- [metavar]rpc_bench[/metavar] must already be installed on each remote machine

[metavar]rpc_bench[/metavar] can call each RPC method multiple times using [metavar]-n <N>[/metavar]
- For each call, parameters are randomized to minimize caching effects"""


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': root_command,
        'help': help_message,
        'args': [
            {
                'name': 'nodes',
                'nargs': '+',
                'help': 'nodes to test, see syntax above',
            },
            {
                'name': ['-m', '--methods'],
                'nargs': '+',
                'help': 'RPC methods to test, space separated list',
            },
            {
                'name': ['-n', '--n-samples'],
                'type': int,
                'dest': 'samples',
                'default': 1,
                'help': 'number of times to call each method',
            },
            {
                'name': ['-s', '--seed'],
                'dest': 'random_seed',
                'help': 'random seed to use for call parameters',
            },
            {
                'name': ['-o', '--output'],
                'dest': 'output_file',
                'help': 'output JSON file to save results',
            },
        ],
        'examples': [
            'localhost:8545 localhost:8546 localhost:8547',
            'localhost:8545 -n 10',
            'localhost:8545 -o results.json',
        ],
    }


def root_command(
    nodes: typing.Sequence[str],
    methods: typing.Sequence[str] | None,
    samples: int | None = None,
    verbose: bool = True,
    output_file: str | None = None,
    random_seed: int | None = None,
) -> None:
    rpc_bench.run_latency_benchmark(
        nodes=nodes,
        methods=methods,
        samples=samples,
        random_seed=random_seed,
        output_file=output_file,
    )

