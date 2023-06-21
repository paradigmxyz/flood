from __future__ import annotations

import typing

import flood
from flood.runners.single_runner import single_runner_execution
# from flood.runners.multi_runner import multi_runner_execution


def run(
    test_name: str,
    *,
    nodes: flood.NodesShorthand | None,
    random_seed: flood.RandomSeed | None = None,
    verbose: bool | int = True,
    rates: typing.Sequence[int] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    mode: flood.LoadTestMode | None = None,
    vegeta_kwargs: flood.VegetaKwargsShorthand | None = None,
    dry: bool,
    output_dir: str | bool | None = None,
    figures: bool = True,
    metrics: typing.Sequence[str] | None = None,
    include_raw_output: bool = False,
    deep_check: bool = False,
) -> None:
    """generate and run tests against nodes"""
    import os

    # get output_dir
    output_dir = _get_output_dir(output_dir)

    # run test from path
    if os.path.exists(test_name) or '/' in test_name:
        (
            test_name,
            path_spec,
            test,
            nodes,
        ) = _load_old_test_data(test_name=test_name, nodes=nodes)
        return single_runner_execution._run_single(
            rerun_of=path_spec,
            test=test,
            #
            test_name=test_name,
            nodes=nodes,
            random_seed=random_seed,
            dry=dry,
            output_dir=output_dir,
            verbose=verbose,
            metrics=metrics,
            figures=figures,
            include_raw_output=include_raw_output,
            deep_check=deep_check,
        )

    if nodes is None:
        raise Exception('must specify nodes')

    if test_name in flood.get_single_test_generators():
        single_runner_execution._run_single(
            rates=rates,
            duration=duration,
            durations=durations,
            vegeta_kwargs=vegeta_kwargs,
            #
            test_name=test_name,
            nodes=nodes,
            random_seed=random_seed,
            dry=dry,
            output_dir=output_dir,
            verbose=verbose,
            metrics=metrics,
            figures=figures,
            include_raw_output=include_raw_output,
            deep_check=deep_check,
        )
    elif test_name in flood.get_multi_test_generators():
        raise NotImplementedError()
    else:
        raise Exception('invalid test name')


def _get_output_dir(output_dir: str | bool | None) -> str | None:
    import os

    if isinstance(output_dir, bool):
        if output_dir:
            import tempfile

            output_dir = tempfile.mkdtemp()
        else:
            output_dir = None
    if output_dir is not None:
        output_dir = os.path.abspath(os.path.expanduser(output_dir))

    return output_dir


def _load_old_test_data(
    test_name: str, nodes: flood.NodesShorthand | None
) -> tuple[str, str, flood.LoadTest, flood.NodesShorthand]:
    path_spec = test_name

    try:
        test_payload = flood.load_single_run_test_payload(path_spec)
        test = test_payload['test']
        test_name = test_payload['name']
    except Exception:
        raise Exception('invalid test path: ' + str(path_spec))

    # use old nodes if none specified
    if nodes is None:
        results_payload = flood.load_single_run_results_payload(path_spec)
        nodes = results_payload['nodes']

    return (test_name, path_spec, test, nodes)

