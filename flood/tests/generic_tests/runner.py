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
    import os
    import toolstr

    # parse inputs
    nodes = flood.parse_nodes(nodes)

    # create test
    if test is not None:
        test_data = flood.parse_test_data(test=test)
        rates = test_data['rates']
        durations = test_data['durations']
        vegeta_kwargs = test_data['vegeta_kwargs']
    else:
        if test_name is None:
            raise Exception('must specify test or test_name')
        rates, durations = flood.generate_timings(
            rates=rates,
            duration=duration,
            durations=durations,
            mode=mode,
        )
        test = flood.generate_test(
            test_name=test_name,
            constants={
                'rates': rates,
                'durations': durations,
                'vegeta_kwargs': vegeta_kwargs,
            },
        )

    # print preamble
    if verbose:
        _print_single_run_preamble(
            test_name=test_name,
            rerun_of=rerun_of,
            rates=rates,
            durations=durations,
            vegeta_kwargs=vegeta_kwargs,
            output_dir=output_dir,
            nodes=nodes,
        )

        if output_dir is not None:
            summary_path = os.path.join(output_dir, 'summary.txt')
            with toolstr.write_stdout_to_file(summary_path):
                _print_single_run_preamble(
                    test_name=test_name,
                    rerun_of=rerun_of,
                    rates=rates,
                    durations=durations,
                    vegeta_kwargs=vegeta_kwargs,
                    output_dir=output_dir,
                    nodes=nodes,
                )

    # save test to disk
    if output_dir is not None:
        file_io._save_single_run_test(
            test_name=test_name, output_dir=output_dir, test=test
        )

    # skip dry run
    if dry:
        return

    # run tests
    try:
        results = flood.run_load_tests(
            nodes=nodes,
            test=test,
            verbose=verbose,
        )
    except Exception as e:
        import traceback

        print('THIS WAS THE ERROR:', e.args)
        print()
        print(traceback.format_exc())
        print()
        print("ERROR OVER")
        raise e

    # output results to file
    if output_dir is not None:
        file_io._save_single_run_results(
            output_dir=output_dir,
            test=test,
            nodes=nodes,
            results=results,
        )

        if figures:
            figures_dir = file_io.get_single_run_figures_path(
                output_dir=output_dir
            )
            flood.plot_load_test_results(
                outputs=results,
                test_name=test_name,
                output_dir=figures_dir,
            )

    # print summary
    if verbose:
        _print_single_run_conclusion(
            output_dir=output_dir,
            results=results,
            metrics=metrics,
            verbose=verbose,
            figures=figures,
        )
        with toolstr.write_stdout_to_file(summary_path, mode='a'):
            _print_single_run_conclusion(
                output_dir=output_dir,
                results=results,
                metrics=metrics,
                verbose=verbose,
                figures=figures,
            )


#
# # printing outputs
#


def _print_single_run_preamble(
    *,
    test_name: str,
    rates: typing.Sequence[int],
    durations: typing.Sequence[int],
    vegeta_kwargs: flood.VegetaKwargsShorthand | None,
    nodes: flood.Nodes,
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

    if len(nodes) == 1:
        node = list(nodes.values())[0]
        toolstr.print_bullet(
            key='node',
            value=_get_node_str(node),
            styles=flood.styles,
        )
    else:
        toolstr.print_bullet(key='nodes', value='', styles=flood.styles)
        for n, node in enumerate(nodes.values()):
            toolstr.print(
                toolstr.add_style(str(n + 1), flood.styles['metavar'])
                + '. '
                + _get_node_str(node),
                indent=4,
                style=flood.styles['description'],
            )

    print()
    print()
    toolstr.print_header(
        'Running load tests...',
        style=flood.styles['content'],
        text_style=flood.styles['metavar'],
    )


def _get_node_str(node: flood.Node) -> str:
    node_str = '"' + node['name'] + '", url=' + node['url']
    remote = node['remote']
    if remote is not None:
        node_str += ' remote=' + remote
    return node_str


def _print_single_run_conclusion(
    output_dir: str | None,
    results: typing.Mapping[str, flood.LoadTestOutput],
    metrics: typing.Sequence[str] | None,
    verbose: bool | int,
    figures: bool,
) -> None:
    import os
    import toolstr

    print('Load tests completed.')

    # print message about metrics file
    if output_dir is not None:
        test_path = file_io.get_single_run_test_path(output_dir=output_dir)
        result_path = file_io.get_single_run_results_path(output_dir=output_dir)
        figures_path = file_io.get_single_run_figures_path(
            output_dir=output_dir
        )

        print()
        print()
        toolstr.print_bullet(
            key='Saving results',
            value='',
            styles=flood.styles,
            bullet_str='',
        )
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
    print('Summarizing performance metrics...')
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
    )

