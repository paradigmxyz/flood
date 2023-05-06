from __future__ import annotations

import typing

import toolcli

import rpc_bench

help_message = """Benchmark a set of node endpoints

[bold][title]Node Specification[/bold][/title]
Basic node syntax is [metavar]url[/metavar] or [metavar]name=url[/metavar]
- The [metavar]name[/metavar] of each node is used for benchmark summary report
- Can specify multiple nodes in space-separated list

[bold][title]Remote Usage[/bold][/title]
[metavar]rpc_bench[/metavar] can be invoked on remote machines
- Use node syntax [metavar]user@remote:node_url[/metavar] or [metavar]name=user@remote:node_url[/metavar]
- Can omit the [metavar]user@[/metavar] prefix if ssh config has username specified
- [metavar]rpc_bench[/metavar] must already be installed on each remote machine

[bold][title]Parameter Randomization[/bold][/title]
[metavar]rpc_bench[/metavar] can call each RPC method multiple times using [metavar]-n <N>[/metavar]
- For each call, parameters are randomized to minimize caching effects
- Specify random seed [metavar]-s <seed>[/metavar] for repeatable set of randomized calls"""


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
                'name': ['-c', '--calls'],
                'dest': 'calls_file',
                'help': 'calls plan JSON file',
            },
            {
                'name': ['-o', '--output'],
                'dest': 'output_file',
                'help': 'output JSON file to save results',
            },
            {
                'name': ['-q', '--quiet'],
                'help': 'do not print any output to STDOUT',
                'action': 'store_true',
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
    samples: int | None,
    calls_file: str | None,
    output_file: str | None,
    random_seed: int | None,
    quiet: bool,
) -> None:
    rpc_bench.run_latency_benchmark(
        nodes=nodes,
        methods=methods,
        samples=samples,
        calls_file=calls_file,
        output_file=output_file,
        random_seed=random_seed,
        verbose=not quiet,
    )

