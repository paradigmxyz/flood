"""

TODO
--methods parameter to specify methods
"""
from __future__ import annotations

import typing

import toolcli

import rpc_bench

help_message = """Load test JSON RPC endpoints

[bold][title]Node Specification[/bold][/title]
- Nodes are specified as a space-separated list
- Basic node syntax is [metavar]url[/metavar] or [metavar]name=url[/metavar]
- The [metavar]name[/metavar] of each node is used for benchmark summary report

[bold][title]Remote Usage[/bold][/title]
- [metavar]rpc_bench[/metavar] can be invoked on remote machines
- Use node syntax [metavar]user@remote:node_url[/metavar] or [metavar]name=user@remote:node_url[/metavar]
- Can omit the [metavar]user@[/metavar] prefix if ssh config has username specified
- [metavar]rpc_bench[/metavar] must already be installed on each remote machine

[bold][title]Parameter Randomization[/bold][/title]
- [metavar]rpc_bench[/metavar] can call each RPC method multiple times using [metavar]-n <N>[/metavar]
- For each call, parameters are randomized to minimize caching effects
- Specify random seed [metavar]-s <seed>[/metavar] for repeatable set of randomized calls"""


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': root_command,
        'help': help_message,
        'args': [
            {
                'name': 'test',
                'help': 'test to run (use [metavar]rpc_bench ls[/metavar] for list)',
            },
            {
                'name': 'nodes',
                'nargs': '+',
                'help': 'nodes to test, see syntax above',
            },
            {
                'name': ['-s', '--seed'],
                'dest': 'random_seed',
                'help': 'random seed to use, default is current timestamp',
            },
            {
                'name': ['-q', '--quiet'],
                'help': 'do not print output to [metavar]STDOUT[/metavar]',
                'action': 'store_true',
            },
            {
                'name': ['-m', '--mode'],
                'help': 'stress, spike, soak, latency, or equality',
            },
            {
                'name': ['-r', '--rates'],
                'help': 'rates to use in load test (requests per second)',
            },
            {
                'name': ['-d', '--duration'],
                'help': 'amount of time to test each rate',
            },
            {
                'name': ['--dry'],
                'help': 'only construct tests, do not run them',
                'action': 'store_true',
            },
            {
                'name': ['-o', '--output'],
                'help': 'directory to save results, default is tmp dir',
            },
        ],
        'examples': [
            'eth_getBlockByNumber localhost:8545',
            'eth_getLogs localhost:8545 localhost:8546 localhost:8547',
        ],
    }


def root_command(
    test: str,
    nodes: typing.Sequence[str],
    output: str | None,
    mode: str | None,
    rates: typing.Sequence[str] | None,
    duration: str | None,
    random_seed: int | None,
    dry: bool | None,
    quiet: bool,
) -> None:

    rpc_bench.run(
        test=test,
        mode=mode,
        nodes=nodes,
        random_seed=random_seed,
        verbose=(not quiet),
        rates=rates,
        duration=duration,
        dry=dry,
        output=output,
    )

