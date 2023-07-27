from __future__ import annotations

import typing

import flood
from flood import generators
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
    vegeta_args: flood.VegetaArgsShorthand | None = None,
    dry: bool = False,
    output_dir: str | None = None,
    figures: bool = True,
    metrics: typing.Sequence[str] | None = None,
    include_deep_output: typing.Sequence[flood.DeepOutput] | None = None,
    deep_check: bool = False,
) -> flood.RunOutput:
    """generate and run tests against nodes"""
    import os

    # get output_dir
    use_output_dir = _get_output_dir(output_dir)

    # run test from path
    if os.path.exists(test_name) or '/' in test_name:
        (
            test_name,
            path_spec,
            test,
            nodes,
        ) = _load_old_test_data(test_name=test_name, nodes=nodes)
        output = single_runner_execution._run_single(
            rerun_of=path_spec,
            test=test,
            #
            test_name=test_name,
            nodes=nodes,
            random_seed=random_seed,
            dry=dry,
            output_dir=use_output_dir,
            verbose=verbose,
            metrics=metrics,
            figures=figures,
            include_deep_output=include_deep_output,
            deep_check=deep_check,
        )
        return {'single_run': output}

    # generate new test
    else:
        if nodes is None:
            raise Exception('must specify nodes')

        if test_name in generators.get_single_test_generators():
            output = single_runner_execution._run_single(
                rates=rates,
                duration=duration,
                durations=durations,
                vegeta_args=vegeta_args,
                #
                test_name=test_name,
                nodes=nodes,
                random_seed=random_seed,
                dry=dry,
                output_dir=use_output_dir,
                verbose=verbose,
                metrics=metrics,
                figures=figures,
                include_deep_output=include_deep_output,
                deep_check=deep_check,
            )
            return {'single_run': output}
        elif test_name in generators.get_multi_test_generators():
            raise NotImplementedError('multi tests not supported yet')
        else:
            raise Exception('invalid test name')


def _get_output_dir(output_dir: str | None) -> str:
    import os

    if output_dir is None:
        import tempfile

        use_output_dir = tempfile.mkdtemp()
    else:
        use_output_dir = output_dir
    return os.path.abspath(os.path.expanduser(use_output_dir))


def _load_old_test_data(
    test_name: str, nodes: flood.NodesShorthand | None
) -> tuple[str, str, flood.LoadTest, flood.NodesShorthand]:
    path_spec = test_name

    try:
        test_payload = flood.load_single_run_test_payload(path_spec)
        test = generators.generate_test(**test_payload['test_parameters'])
        test_name = test_payload['name']
    except Exception:
        raise Exception('invalid test path: ' + str(path_spec))

    # use old nodes if none specified
    if nodes is None:
        results_payload = flood.load_single_run_results_payload(path_spec)
        nodes = results_payload['nodes']

    return (test_name, path_spec, test, nodes)

