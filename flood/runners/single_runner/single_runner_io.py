from __future__ import annotations

import typing

import flood

if typing.TYPE_CHECKING:
    import polars as pl


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
    test: flood.LoadTest,
) -> None:
    import os
    import json

    if not os.path.isdir(output_dir):
        if os.path.exists(output_dir):
            raise Exception('output must be a directory path')
        else:
            os.makedirs(output_dir, exist_ok=True)

    path = _path_templates['single_run_test'].format(output_dir=output_dir)
    payload: flood.SingleRunTestPayload = {
        'version': flood.__version__,
        'type': 'single_test',
        'name': test_name,
        'test': test,
    }
    with open(path, 'w') as f:
        json.dump(payload, f)


def _save_single_run_results(
    *,
    output_dir: str,
    test: flood.LoadTest,
    nodes: flood.Nodes,
    results: typing.Mapping[str, flood.LoadTestOutput],
    figures: bool,
    test_name: str,
) -> None:
    import os
    import json

    if not os.path.isdir(output_dir):
        if os.path.exists(output_dir):
            raise Exception('output must be a directory path')
        else:
            os.makedirs(output_dir)

    path = _path_templates['single_run_results'].format(output_dir=output_dir)
    payload: flood.SingleRunResultsPayload = {
        'version': flood.__version__,
        'type': 'single_test',
        'nodes': nodes,
        'results': results,
    }
    with open(path, 'w') as f:
        json.dump(payload, f)

    if figures:
        figures_dir = get_single_run_figures_path(output_dir=output_dir)
        colors = flood.get_nodes_plot_colors(nodes=nodes)
        flood.plot_load_test_results(
            outputs=results,
            test_name=test_name,
            output_dir=figures_dir,
            colors=colors,
        )


def load_single_run_test_payload(
    path_spec: str,
) -> flood.SingleRunTestPayload:
    import os
    import json

    if os.path.isfile(path_spec):
        path = path_spec
    else:
        path = get_single_run_test_path(path_spec)
    with open(path) as f:
        test: flood.SingleRunTestPayload = json.load(f)
    return test


def load_single_run_test(
    output_dir: str,
) -> flood.LoadTest:
    payload = load_single_run_test_payload(output_dir)
    return payload['test']


def load_single_run_results_payload(
    output_dir: str,
) -> flood.SingleRunResultsPayload:
    import json

    path = get_single_run_results_path(output_dir=output_dir)
    with open(path) as f:
        results: flood.SingleRunResultsPayload = json.load(f)
    return results


def load_single_run_results(
    output_dir: str,
) -> typing.Mapping[str, flood.LoadTestOutput]:
    payload = load_single_run_results_payload(output_dir=output_dir)
    return payload['results']


def load_single_run_raw_output(
    *,
    output_dir: str | None = None,
    results: typing.Mapping[str, flood.LoadTestOutput] | None = None,
    sample_index: int | None = None,
) -> typing.Mapping[str, pl.DataFrame]:
    import polars as pl

    if results is None:
        if output_dir is None:
            raise Exception('must specify output_dir or results')
        results = load_single_run_results(output_dir=output_dir)
    node_dfs = {}
    for node_name, node_results in results.items():
        raw_output = node_results['raw_output']
        if raw_output is None:
            raise Exception('raw_outputs were not saved for test')
        else:
            if sample_index is not None:
                indices = [sample_index]
            else:
                indices = list(range(len(raw_output)))
            dfs = []
            for index in indices:
                item = raw_output[index]
                if item is None:
                    raise Exception('raw_outputs were not saved for test')
                decoded = flood.decode_raw_vegeta_output(item)
                df = flood.convert_raw_vegeta_output_to_dataframe(decoded)
                df = df.with_columns(pl.lit(index).alias('sample_index'))
                dfs.append(df)
            node_dfs[node_name] = pl.concat(dfs)
    return node_dfs

