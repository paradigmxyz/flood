from __future__ import annotations

import typing

import toolcli

import flood


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': print_command,
        'help': 'print output of previous test results',
        'args': [
            {
                'name': 'output_dirs',
                'help': 'output directory of previous test(s)',
                'nargs': '+',
            },
            {
                'name': ('-m', '--metrics'),
                'help': 'space-separated list of performance metrics',
                'nargs': '+',
            },
        ],
    }


def print_command(
    output_dirs: typing.Sequence[str], metrics: typing.Sequence[str]
) -> None:
    if len(output_dirs) == 1:
        print_single(output_dirs[0], metrics)
    elif len(output_dirs) > 1:
        print_multiple(output_dirs)
    else:
        raise Exception('must specify at least one output_dir')


def print_single(
    output_dir: str, metrics: typing.Sequence[str]
) -> None:
    test_payload = flood.load_single_run_test_payload(output_dir)
    test = flood.generate_test(**test_payload['test_parameters'])
    results_payload = flood.load_single_run_results_payload(output_dir)
    results = results_payload['results']

    # print test summary
    flood.runners.single_runner.single_runner_summary._print_single_run_preamble_copy(
        test_name=test_payload['name'],
        rates=[subtest['rate'] for subtest in test['attacks']],
        durations=[subtest['duration'] for subtest in test['attacks']],
        vegeta_args=[subtest['vegeta_args'] for subtest in test['attacks']],
        output_dir=output_dir,
    )

    # print node data
    print()
    flood.user_io.print_header('Nodes tested')
    flood.user_io.print_nodes_table(results_payload['nodes'])

    # decide metrics
    if metrics is None:
        metrics = ['success', 'throughput', 'p90']

    # print performance metrics
    print()
    print()
    flood.user_io.print_header('Summarizing performance metrics...')
    flood.user_io.print_metric_tables(
        results=results,
        metrics=metrics,
        indent=4,
    )


def print_multiple(output_dirs: typing.Sequence[str]) -> None:
    # load results
    test_payloads = []
    outputs = []
    for output_dir in output_dirs:
        test_payload = flood.load_single_run_test_payload(output_dir)
        output = flood.load_single_run_results_payload(output_dir)
        test_payloads.append(test_payload)
        outputs.append(output)

    # print max throughput
    rows = []
    conditions = list(outputs[0]['results'].keys())
    for test_payload, output in zip(test_payloads, outputs):
        test_parameters = test_payload['test_parameters']
        row: list[typing.Any] = [test_parameters['test_name']]
        for condition in conditions:
            results = output['results'][condition]
            throughputs = [tp for tp in results['throughput'] if tp is not None]
            if len(throughputs) > 0:
                row.append(max(throughputs))
            else:
                row.append(None)
        row.append(max(results['target_rate']))
        rows.append(row)
    labels = ['test'] + conditions + ['max tested']

    flood.user_io.print_text_box('Max Throughput')
    print()
    print('units = requests per second')
    print()
    flood.user_io.print_table(rows, labels=labels)

