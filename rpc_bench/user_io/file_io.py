from __future__ import annotations

import typing

import rpc_bench


_path_templates = {
    'single_run_test': '{output_dir}/test.json',
    'single_run_results': '{output_dir}/results.json',
    'single_run_figures_dir': '{output_dir}/figures',
}


def get_single_run_test_path(output_dir: str) -> str:
    return _path_templates['single_run_test'].format(output_dir=output_dir)


def get_single_run_results_path(output_dir: str) -> str:
    return _path_templates['single_run_results'].format(output_dir=output_dir)


def get_single_run_figures_path(output_dir: str) -> str:
    return _path_templates['single_run_figures_dir'].format(
        output_dir=output_dir
    )


def _save_single_run_test(
    test_name: str,
    output_dir: str,
    test: rpc_bench.LoadTest,
) -> None:
    import os
    import json

    if not os.path.isdir(output_dir):
        if os.path.exists(output_dir):
            raise Exception('output must be a directory path')
        else:
            os.makedirs(output_dir, exist_ok=True)

    path = _path_templates['single_run_test'].format(output_dir=output_dir)
    payload = {
        'version': rpc_bench.__version__,
        'type': 'single_test',
        'name': test_name,
        'test': test,
    }
    with open(path, 'w') as f:
        json.dump(payload, f)


def _save_single_run_results(
    output_dir: str,
    test: rpc_bench.LoadTest,
    nodes: rpc_bench.Nodes,
    results: typing.Mapping[str, rpc_bench.LoadTestOutput],
) -> None:
    import os
    import json

    if not os.path.isdir(output_dir):
        if os.path.exists(output_dir):
            raise Exception('output must be a directory path')
        else:
            os.makedirs(output_dir)

    path = _path_templates['single_run_results'].format(output_dir=output_dir)
    payload = {
        'version': rpc_bench.__version__,
        'type': 'single_test',
        'test': test,
        'nodes': nodes,
        'results': results,
    }
    with open(path, 'w') as f:
        json.dump(payload, f)


def load_single_test_results(
    output_dir: str,
) -> typing.Mapping[str, rpc_bench.LoadTestOutput]:
    import json

    path = get_single_run_results_path(output_dir=output_dir)
    with open(path) as f:
        results: typing.Mapping[str, rpc_bench.LoadTestOutput] = json.load(f)
    return results

