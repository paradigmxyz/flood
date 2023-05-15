from __future__ import annotations

import typing

import rpc_bench


def run(
test_name: str,
    *,
    nodes: rpc_bench.NodesShorthand,
    random_seed: rpc_bench.RandomSeed | None = None,
    verbose: bool,
    rates: typing.Sequence[int] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    mode: rpc_bench.LoadTestMode | None = None,
    vegeta_kwargs: rpc_bench.VegetaKwargsShorthand | None = None,
    dry: bool,
    output: str | None = None,
) -> None:
    """generate and run load test(s) against node(s)"""

    import os

    # output test design to file
    if output is not None:
        if not os.path.isdir(output):
            if os.path.exists(output):
                raise Exception('output must be a directory path')
            else:
                os.makedirs(output)


    # generate tests
    if test_name in rpc_bench.get_single_test_generators():
        _run_single(
            test_name=test_name,
            nodes=nodes,
            random_seed=random_seed,
            rates=rates,
            durations=durations,
            vegeta_kwargs=vegeta_kwargs,
            dry=dry,
            output=output,
            verbose=verbose,
        )
    elif test_name in rpc_bench.get_multi_test_generators():
        raise NotImplementedError()
    else:
        raise Exception('invalid test name')


def _run_single(
    *,
    test_name: str,
    nodes: rpc_bench.NodesShorthand,
    random_seed: rpc_bench.RandomSeed | None = None,
    rates: typing.Sequence[int] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    mode: rpc_bench.LoadTestMode | None = None,
    vegeta_kwargs: rpc_bench.VegetaKwargsShorthand | None = None,
    dry: bool,
    output: str | None = None,
    verbose: bool,
) -> None:
    import os
    import json

    # create timing
    rates, durations = rpc_bench.generate_timings(
        rates=rates,
        duration=duration,
        durations=durations,
        mode=mode,
    )

    # create test
    test = rpc_bench.generate_test(
        test_name=test_name,
        constants={
            'rates': rates,
            'durations': durations,
            'vegeta_kwargs': vegeta_kwargs,
        },
    )

    # save outputs to disk
    if output is not None:
        test_design_path = os.path.join(output, 'test.json')
        test_payload = {
            'version': rpc_bench.__version__,
            'type': 'single_test',
            'test': test,
        }
        with open(test_design_path, 'w') as f:
            json.dump(test_payload, f)

    # run tests
    if not dry:

        nodes = rpc_bench.parse_nodes(nodes)

        # run tests
        results = {}
        for node_name, node in nodes.items():
            results[node_name] = rpc_bench.run_load_test(
                node=node,
                test=test,
                verbose=verbose,
            )

        # output results to file
        if output is not None:
            result_path = os.path.join(output, 'results.json')
            result_payload = {
                'type': 'single_test',
                'test': test,
                'nodes': nodes,
                'results': results,
            }
            with open(result_path, 'w') as f:
                json.dump(result_payload, f)

