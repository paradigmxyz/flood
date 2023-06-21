from __future__ import annotations

import typing

import toolcli

import flood


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': print_command,
        'help': 'print output of previous test results',
        'args': [
            {'name': 'output_dir', 'help': 'output directory of previous test'},
            {
                'name': ('-m', '--metrics'),
                'help': 'space-separated list of performance metrics',
                'nargs': '+',
            },
        ],
    }


def print_command(output_dir: str, metrics: typing.Sequence[str]) -> None:

    test_payload = flood.load_single_run_test_payload(output_dir)
    test = test_payload['test']
    results_payload = flood.load_single_run_results_payload(output_dir)
    results = results_payload['results']

    # print test summary
    flood.runners.single_runner.single_runner_summary._print_single_run_preamble_copy(
        test_name=test_payload['name'],
        rates=[subtest['rate'] for subtest in test],
        durations=[subtest['duration'] for subtest in test],
        vegeta_kwargs=[subtest['vegeta_kwargs'] for subtest in test],
        output_dir=output_dir,
    )

    # print node data
    print()
    flood.print_header('Nodes tested')
    flood.print_nodes_table(results_payload['nodes'])

    # decide metrics
    if metrics is None:
        metrics = ['success', 'throughput', 'p90']

    # print performance metrics
    print()
    print()
    flood.print_header('Summarizing performance metrics...')
    flood.print_metric_tables(
        results=results,
        metrics=metrics,
        indent=4,
    )

