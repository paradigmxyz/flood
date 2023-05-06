from __future__ import annotations

import typing

import toolcli

import rpc_bench


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': root_command,
        'help': 'run RPC benchmark',
        'args': [
            {
                'name': 'nodes',
                'nargs': '+',
                'help': 'nodes to test',
            },
            {
                'name': ['-m', '--methods'],
                'nargs': '+',
                'help': 'RPC methods to test, see syntax above',
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
                'help': 'output JSON file where to save results',
            },
        ],
    }


def root_command(
    nodes: typing.Sequence[str] | typing.Mapping[str, str],
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

