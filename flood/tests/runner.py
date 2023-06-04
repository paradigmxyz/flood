from __future__ import annotations

import typing

import flood
from flood.user_io import file_io


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
) -> None:
    """generate and run load test(s) against node(s)"""
    import json
    import os

    if isinstance(output_dir, bool):
        if output_dir:
            import tempfile

            output_dir = tempfile.mkdtemp()
        else:
            output_dir = None
    if output_dir is not None:
        output_dir = os.path.abspath(os.path.expanduser(output_dir))

    # run test from path
    if os.path.exists(test_name) or '/' in test_name:
        path_spec = test_name
        if os.path.isdir(path_spec):
            test_path = flood.get_single_run_test_path(output_dir=path_spec)
        else:
            test_path = path_spec
        try:
            with open(test_path, 'r') as f:
                test_payload = json.load(f)
            test = test_payload['test']
            test_name = test_payload['name']
        except Exception:
            raise Exception('invalid test path: ' + str(test_path))

        if nodes is None:
            if os.path.isdir(path_spec):
                result_path = flood.get_single_run_results_path(
                    output_dir=path_spec,
                )
            else:
                result_path = path_spec
            try:
                with open(result_path, 'r') as f:
                    test_payload = json.load(f)
                nodes = test_payload['nodes']
            except Exception:
                raise Exception('invalid test path: ' + str(result_path))

        return _run_single(
            test_name=test_name,
            rerun_of=path_spec,
            test=test,
            nodes=nodes,
            random_seed=random_seed,
            dry=dry,
            output_dir=output_dir,
            verbose=verbose,
            metrics=metrics,
            figures=figures,
        )

    if nodes is None:
        raise Exception('must specify nodes')

    if test_name in flood.get_single_test_generators():
        _run_single(
            test_name=test_name,
            nodes=nodes,
            random_seed=random_seed,
            rates=rates,
            duration=duration,
            durations=durations,
            vegeta_kwargs=vegeta_kwargs,
            dry=dry,
            output_dir=output_dir,
            verbose=verbose,
            metrics=metrics,
            figures=figures,
        )
    elif test_name in flood.get_multi_test_generators():
        raise NotImplementedError()
    else:
        raise Exception('invalid test name')


def _run_single(
    *,
    test_name: str,
    rerun_of: str | None = None,
    test: flood.LoadTest | None = None,
    nodes: flood.NodesShorthand,
    random_seed: flood.RandomSeed | None = None,
    rates: typing.Sequence[int] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    mode: flood.LoadTestMode | None = None,
    vegeta_kwargs: flood.VegetaKwargsShorthand | None = None,
    dry: bool,
    output_dir: str | None = None,
    figures: bool,
    metrics: typing.Sequence[str] | None = None,
    verbose: bool | int,
) -> None:
    # get test parameters
    rates, durations, vegeta_kwargs = _get_single_test_parameters(
        test=test,
        rates=rates,
        duration=duration,
        durations=durations,
        mode=mode,
    )

    # print preamble
    if verbose:
        _print_single_run_preamble_copy(
            test_name=test_name,
            rerun_of=rerun_of,
            rates=rates,
            durations=durations,
            vegeta_kwargs=vegeta_kwargs,
            output_dir=output_dir,
        )

    # parse nodes
    nodes = flood.parse_nodes(nodes, verbose=verbose, request_metadata=True)

    # generate test and save to disk
    if test is None:
        test = flood.generate_test(
            test_name=test_name,
            rates=rates,
            durations=durations,
            vegeta_kwargs=vegeta_kwargs,
            network=flood.parse_nodes_network(nodes),
            random_seed=random_seed,
            output_dir=output_dir,
        )

    # skip dry run
    if dry:
        return

    # run tests
    if verbose:
        _print_run_start()
    results = flood.run_load_tests(nodes=nodes, test=test, verbose=verbose)

    # output results to file
    if output_dir is not None:
        file_io._save_single_run_results(
            output_dir=output_dir,
            test=test,
            nodes=nodes,
            results=results,
            figures=figures,
            test_name=test_name,
        )

    # print summary
    if verbose:
        _print_single_run_conclusion_copy(
            output_dir=output_dir,
            results=results,
            metrics=metrics,
            verbose=verbose,
            figures=figures,
        )


#
# # helper functions
#


def _get_single_test_parameters(
    test: flood.LoadTest | None = None,
    rates: typing.Sequence[int] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    mode: flood.LoadTestMode | None = None,
    vegeta_kwargs: flood.VegetaKwargsShorthand | None = None,
) -> tuple[
    typing.Sequence[int],
    typing.Sequence[int],
    flood.VegetaKwargsShorthand | None,
]:
    if test is not None:
        test_data = flood.parse_test_data(test=test)
        rates = test_data['rates']
        durations = test_data['durations']
        vegeta_kwargs = test_data['vegeta_kwargs']
    else:
        rates, durations = flood.generate_timings(
            rates=rates,
            duration=duration,
            durations=durations,
            mode=mode,
        )
    return rates, durations, vegeta_kwargs


#
# # printing outputs
#


def _print_single_run_preamble(
    *,
    test_name: str,
    rates: typing.Sequence[int],
    durations: typing.Sequence[int],
    vegeta_kwargs: flood.VegetaKwargsShorthand | None,
    rerun_of: str | None = None,
    output_dir: str | None,
) -> None:
    import os
    import toolstr

    _print_single_run_preamble_copy(
        test_name=test_name,
        rerun_of=rerun_of,
        rates=rates,
        durations=durations,
        vegeta_kwargs=vegeta_kwargs,
        output_dir=output_dir,
    )
    if output_dir is not None:
        summary_path = os.path.join(output_dir, 'summary.txt')
        with toolstr.write_stdout_to_file(summary_path):
            _print_single_run_preamble_copy(
                test_name=test_name,
                rerun_of=rerun_of,
                rates=rates,
                durations=durations,
                vegeta_kwargs=vegeta_kwargs,
                output_dir=output_dir,
            )


def _print_single_run_preamble_copy(
    *,
    test_name: str,
    rates: typing.Sequence[int],
    durations: typing.Sequence[int],
    vegeta_kwargs: flood.VegetaKwargsShorthand | None,
    rerun_of: str | None = None,
    output_dir: str | None,
) -> None:
    import toolstr

    toolstr.print_text_box(
        toolstr.add_style('Load test: ' + test_name, flood.styles['metavar']),
        style=flood.styles['content'],
    )
    toolstr.print_bullet(key='sample rates', value=rates, styles=flood.styles)
    if len(set(durations)) == 1:
        toolstr.print_bullet(
            key='sample duration',
            value=durations[0],
            styles=flood.styles,
        )
    else:
        toolstr.print_bullet(
            key='sample durations', value=durations, styles=flood.styles
        )
    if vegeta_kwargs is None or len(vegeta_kwargs) == 0:
        toolstr.print_bullet(key='extra args', value=None, styles=flood.styles)

    if rerun_of is not None:
        toolstr.print_bullet(
            key='rerun of', value=rerun_of, styles=flood.styles
        )
    toolstr.print_bullet(
        key='output directory', value=output_dir, styles=flood.styles
    )
    print()


def _print_run_start() -> None:
    import datetime
    import toolstr

    print()
    print()
    toolstr.print_header(
        'Running load tests...',
        style=flood.styles['content'],
        text_style=flood.styles['metavar'],
    )
    dt = datetime.datetime.now()
    if dt.microsecond >= 500_000:
        dt = dt + datetime.timedelta(microseconds=1_000_000 - dt.microsecond)
    else:
        dt = dt - datetime.timedelta(microseconds=dt.microsecond)
    timestamp = (
        toolstr.add_style('\[', flood.styles['content'])
        + toolstr.add_style(str(dt), flood.styles['metavar'])
        + toolstr.add_style(']', flood.styles['content'])
    )
    toolstr.print(timestamp + ' Starting')


def _print_single_run_conclusion(
    *,
    output_dir: str | None,
    results: typing.Mapping[str, flood.LoadTestOutput],
    metrics: typing.Sequence[str] | None,
    verbose: bool | int,
    figures: bool,
) -> None:
    _print_single_run_conclusion_copy(
        output_dir=output_dir,
        results=results,
        metrics=metrics,
        verbose=verbose,
        figures=figures,
    )
    if output_dir is not None:
        import os
        import toolstr

        summary_path = os.path.join(output_dir, 'summary.txt')
        with toolstr.write_stdout_to_file(summary_path, mode='a'):
            _print_single_run_conclusion_copy(
                output_dir=output_dir,
                results=results,
                metrics=metrics,
                verbose=verbose,
                figures=figures,
            )


def _print_single_run_conclusion_copy(
    output_dir: str | None,
    results: typing.Mapping[str, flood.LoadTestOutput],
    metrics: typing.Sequence[str] | None,
    verbose: bool | int,
    figures: bool,
) -> None:
    import datetime
    import os
    import toolstr

    dt = datetime.datetime.now()
    if dt.microsecond >= 500_000:
        dt = dt + datetime.timedelta(microseconds=1_000_000 - dt.microsecond)
    else:
        dt = dt - datetime.timedelta(microseconds=dt.microsecond)
    timestamp = (
        toolstr.add_style('\[', flood.styles['content'])
        + toolstr.add_style(str(dt), flood.styles['metavar'])
        + toolstr.add_style(']', flood.styles['content'])
    )
    toolstr.print(timestamp + ' Load tests completed.')

    # print message about metrics file
    if output_dir is not None:
        test_path = file_io.get_single_run_test_path(output_dir=output_dir)
        result_path = file_io.get_single_run_results_path(output_dir=output_dir)
        figures_path = file_io.get_single_run_figures_path(
            output_dir=output_dir
        )

        print()
        print()
        flood.print_header('Saving results...')
        toolstr.print_bullet(
            key=os.path.relpath(test_path, output_dir),
            value='',
            colon_str='',
            styles=flood.styles,
        )
        toolstr.print_bullet(
            key=os.path.relpath(result_path, output_dir),
            value='',
            colon_str='',
            styles=flood.styles,
        )
        if figures:
            toolstr.print_bullet(
                key=os.path.relpath(figures_path, output_dir),
                value='',
                colon_str='',
                styles=flood.styles,
            )

    # decide metrics
    if metrics is None:
        metrics = ['success', 'throughput', 'p90']

    # print metrics
    print()
    print()
    flood.print_header('Summarizing performance metrics...')
    if verbose > 1:
        toolstr.print_bullet(
            key='metrics shown below',
            value=', '.join(metrics),
            styles=flood.styles,
        )
        example_result = list(results.values())[0]
        additional = [
            key for key in example_result.keys() if key not in metrics
        ]
        toolstr.print_bullet(
            key='additional metrics available',
            value=', '.join(additional),
            styles=flood.styles,
        )

    # print metric values
    print()
    flood.print_metric_tables(
        results=results,
        metrics=metrics,
        indent=4,
    )
