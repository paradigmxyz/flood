"""

TODO
--methods parameter to specify methods
"""
from __future__ import annotations

import typing

import toolcli

import flood

help_message = """Load test JSON RPC endpoints

[bold][title]Test Specification[/bold][/title]
- [metavar]TEST[/metavar] can be a template, use [metavar]flood ls[/metavar] to list test templates
- Alternatively, [metavar]TEST[/metavar] can be a directory path of a previous test
    - This will rerun this the previous test, possibly on new nodes

[bold][title]Node Specification[/bold][/title]
- Nodes are specified as a space-separated list
- Basic node syntax is [metavar]url[/metavar] or [metavar]name=url[/metavar]
- The [metavar]name[/metavar] of each node is used for benchmark summary report

[bold][title]Remote Usage[/bold][/title]
- [metavar]flood[/metavar] can be invoked on remote machines
- Use node syntax [metavar]user@remote:node_url[/metavar] or [metavar]name=user@remote:node_url[/metavar]
- Can omit the [metavar]user@[/metavar] prefix if ssh config has username specified
- [metavar]flood[/metavar] must already be installed on each remote machine

[bold][title]Parameter Randomization[/bold][/title]
- [metavar]flood[/metavar] can call each RPC method multiple times using [metavar]-n <N>[/metavar]
- For each call, parameters are randomized to minimize caching effects
- Specify random seed [metavar]-s <seed>[/metavar] for repeatable set of randomized calls"""  # noqa: E501


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': root_command,
        'help': help_message,
        'args': [
            {
                'name': 'test',
                'help': 'test to run (use [metavar]flood ls[/metavar] for list)',  # noqa: E501
            },
            {
                'name': 'nodes',
                'nargs': '*',
                'help': 'nodes to test, see syntax above',
            },
            {
                'name': ['-s', '--seed'],
                'dest': 'random_seed',
                'type': int,
                'help': 'random seed to use, default is current timestamp',
            },
            {
                'name': ['-q', '--quiet'],
                'help': 'do not print output to [metavar]STDOUT[/metavar]',
                'action': 'store_true',
            },
            {
                'name': ['-e', '--equality'],
                'help': 'run equality test instead of load test',
                'action': 'store_true',
            },
            {
                'name': ['-m', '--mode'],
                'choices': ['stress', 'spike', 'soak'],
                'help': 'load test type: stress, spike, or soak',
            },
            {
                'name': ['-r', '--rates'],
                'nargs': '+',
                'help': 'rates to use in load test (requests per second)',
            },
            {
                'name': ['-d', '--duration'],
                'type': int,
                'help': 'amount of time to test each rate',
            },
            {
                'name': ['-o', '--output'],
                'dest': 'output_dir',
                'help': 'directory to save results, default is tmp dir',
            },
            {
                'name': ['--dry'],
                'help': 'only construct tests, do not run them',
                'action': 'store_true',
            },
            {
                'name': ['--metrics'],
                'nargs': '+',
                'help': 'space-separated list of performance metrics to show',
            },
            {
                'name': ['--no-figures'],
                'help': 'skip generating summary figures in output_dir',
                'dest': 'figures',
                'action': 'store_false',
            },
            {
                'name': ['--save-raw-output'],
                'help': 'save raw output from Vegeta',
                'action': 'store_true',
            },
            {
                'name': ['--deep-check'],
                'help': 'validate the contents of every RPC response',
                'action': 'store_true',
            },
        ],
        'examples': [
            'eth_getBlockByNumber localhost:8545',
            'eth_getLogs localhost:8545 localhost:8546 localhost:8547',
            'all client1=0.0.0.0:8545 client2=0.0.0.0:8546 --equality',
        ],
    }


def root_command(
    test: str,
    nodes: typing.Sequence[str] | None,
    output_dir: str | None,
    metrics: typing.Sequence[str],
    mode: flood.LoadTestMode | None,
    rates: typing.Sequence[int] | typing.Sequence[str] | None,
    duration: int | None,
    random_seed: int | None,
    dry: bool,
    quiet: bool,
    figures: bool,
    equality: bool,
    save_raw_output: bool,
    deep_check: bool,
) -> None:
    verbose = not quiet
    if nodes is not None and len(nodes) == 0:
        nodes = None

    if equality:
        if output_dir is not None:
            raise Exception('output_dir not used in equality test')
        if metrics is not None:
            raise Exception('metrics not used in equality test')
        if mode is not None:
            raise Exception('metrics not used in equality test')
        if rates is not None:
            raise Exception('rates not used in equality test')
        if duration is not None:
            raise Exception('duration not used in equality test')
        if dry:
            raise Exception('dry not used in equality test')
        if not figures:
            raise Exception('figures not used in equality test')
        flood.run_equality_test(
            test_name=test,
            nodes=nodes,
            random_seed=random_seed,
            verbose=verbose,
        )

    else:
        if rates is not None:
            rates = [int(rate) for rate in rates]
        flood.run(
            test_name=test,
            mode=mode,
            nodes=nodes,
            metrics=metrics,
            random_seed=random_seed,
            verbose=verbose,
            rates=rates,
            duration=duration,
            dry=dry,
            output_dir=output_dir or True,
            figures=figures,
            include_raw_output=save_raw_output,
            deep_check=deep_check,
        )

