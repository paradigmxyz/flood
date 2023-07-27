from __future__ import annotations

import typing

import flood


#
# # path utiltiies
#

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


#
# # save utilities
#


def _save_single_run_test(
    test_name: str,
    output_dir: str,
    test_parameters: flood.TestGenerationParameters,
) -> None:
    import os
    import orjson

    if not os.path.isdir(output_dir):
        if os.path.exists(output_dir):
            raise Exception('output must be a directory path')
        else:
            os.makedirs(output_dir, exist_ok=True)

    path = _path_templates['single_run_test'].format(output_dir=output_dir)
    payload: flood.SingleRunTestPayload = {
        'flood_version': flood.__version__,
        'type': 'single_test',
        'name': test_name,
        'test_parameters': test_parameters,
    }
    with open(path, 'wb') as f:
        f.write(orjson.dumps(payload))


def _save_single_run_results(
    *,
    output_dir: str,
    nodes: flood.Nodes,
    results: typing.Mapping[str, flood.LoadTestOutput],
    figures: bool,
    test_name: str,
    t_run_start: float,
    t_run_end: float,
) -> flood.SingleRunResultsPayload:
    import os
    import sys

    import orjson

    if not os.path.isdir(output_dir):
        if os.path.exists(output_dir):
            raise Exception('output must be a directory path')
        else:
            os.makedirs(output_dir)

    path = _path_templates['single_run_results'].format(output_dir=output_dir)
    payload: flood.SingleRunResultsPayload = {
        'flood_version': flood.get_flood_version(),
        'dependency_versions': flood.get_dependency_versions(),
        'cli_args': list(sys.argv),
        'type': 'single_test',
        't_run_start': t_run_start,
        't_run_end': t_run_end,
        'nodes': nodes,
        'results': results,
    }
    with open(path, 'wb') as f:
        f.write(orjson.dumps(payload))

    if figures:
        figures_dir = get_single_run_figures_path(output_dir=output_dir)
        colors = flood.user_io.get_nodes_plot_colors(nodes=nodes)
        flood.tests.load_tests.plot_load_test_results(
            outputs=results,
            test_name=test_name,
            output_dir=figures_dir,
            colors=colors,
        )

    return payload


#
# # load utiltiies
#


def load_single_run_test_payload(
    path_spec: str,
    allow_other_versions: bool = False,
) -> flood.SingleRunTestPayload:
    import os
    import orjson

    if os.path.isfile(path_spec):
        path = path_spec
    else:
        path = get_single_run_test_path(path_spec)
    with open(path, 'rb') as f:
        test: flood.SingleRunTestPayload = orjson.loads(f.read())

    if test['flood_version'] != flood.__version__:
        if allow_other_versions:
            pass
        else:
            raise Exception(
                'loaded test version ('
                + str(test['flood_version'])
                + ') does not match current flood version ('
                + flood.__version__
                + ')'
            )

    return test


def load_single_run_results_payload(
    output_dir: str,
) -> flood.SingleRunResultsPayload:
    import orjson

    path = get_single_run_results_path(output_dir=output_dir)
    with open(path, 'rb') as f:
        results: flood.SingleRunResultsPayload = orjson.loads(f.read())
    return results

