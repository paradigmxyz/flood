from __future__ import annotations

import typing

import flood
from . import single_runner_io


def _print_single_run_preamble(
    *,
    test_name: str,
    rates: typing.Sequence[int],
    durations: typing.Sequence[int],
    vegeta_args: flood.VegetaArgsShorthand | None,
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
        vegeta_args=vegeta_args,
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
                vegeta_args=vegeta_args,
                output_dir=output_dir,
            )


def _print_single_run_preamble_copy(
    *,
    test_name: str,
    rates: typing.Sequence[int],
    durations: typing.Sequence[int],
    vegeta_args: flood.VegetaArgsShorthand | None,
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
    toolstr.print_bullet(
        key='extra args', value=vegeta_args, styles=flood.styles
    )

    if rerun_of is not None:
        toolstr.print_bullet(
            key='rerun of', value=rerun_of, styles=flood.styles
        )
    toolstr.print_bullet(
        key='output directory', value=output_dir, styles=flood.styles
    )
    print()


def _print_run_start() -> None:
    import toolstr

    print()
    print()
    toolstr.print_header(
        'Running load tests...',
        style=flood.styles['content'],
        text_style=flood.styles['metavar'],
    )
    flood.print_timestamped('Starting')


def _print_single_run_conclusion(
    *,
    output_dir: str | None,
    results: typing.Mapping[str, flood.LoadTestOutput],
    metrics: typing.Sequence[str] | None,
    verbose: bool | int,
    figures: bool,
    deep_check: bool,
) -> None:
    _print_single_run_conclusion_text(
        output_dir=output_dir,
        results=results,
        metrics=metrics,
        verbose=verbose,
        figures=figures,
        deep_check=deep_check,
    )
    if output_dir is not None:
        import os
        import toolstr

        summary_path = os.path.join(output_dir, 'summary.txt')
        with toolstr.write_stdout_to_file(summary_path, mode='a'):
            _print_single_run_conclusion_text(
                output_dir=output_dir,
                results=results,
                metrics=metrics,
                verbose=verbose,
                figures=figures,
                deep_check=deep_check,
            )


def _print_single_run_conclusion_text(
    output_dir: str | None,
    results: typing.Mapping[str, flood.LoadTestOutput],
    metrics: typing.Sequence[str] | None,
    verbose: bool | int,
    figures: bool,
    deep_check: bool,
) -> None:
    import os
    import toolstr

    flood.print_timestamped('Load tests completed.')

    # print message about metrics file
    if output_dir is not None:
        test_path = single_runner_io.get_single_run_test_path(
            output_dir=output_dir
        )
        result_path = single_runner_io.get_single_run_results_path(
            output_dir=output_dir
        )
        figures_path = single_runner_io.get_single_run_figures_path(
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
    flood.print_metric_tables(results=results, metrics=metrics, indent=4)

    # deep inspection tables
    if deep_check:
        # extract data per category
        deep_results_by_category: typing.MutableMapping[
            flood.ResponseCategory,
            typing.MutableMapping[str, flood.LoadTestDeepOutput],
        ]
        deep_results_by_category = {}
        for result_name, result in results.items():
            deep_metrics = result['deep_metrics']
            if deep_metrics is not None:
                for category, category_results in deep_metrics.items():
                    deep_results_by_category.setdefault(category, {})
                    deep_results_by_category[category][
                        result_name
                    ] = category_results
            else:
                raise Exception('deep metrics not available')

        metric_names = [
            m for m in metrics if m not in ['success', 'throughput']
        ]
        for (
            category,
            result_category_results,
        ) in deep_results_by_category.items():
            flood.print_metric_tables(
                results=result_category_results,
                metrics=metric_names,
                suffix=', ' + category + ' calls',
                indent=4,
            )

