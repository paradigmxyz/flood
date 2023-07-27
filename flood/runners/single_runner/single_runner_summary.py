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

    styles = flood.user_io.styles

    toolstr.print_text_box(
        toolstr.add_style('Load test: ' + test_name, styles['metavar']),
        style=flood.user_io.styles['content'],
    )
    toolstr.print_bullet(key='sample rates', value=rates, styles=styles)
    if len(set(durations)) == 1:
        toolstr.print_bullet(
            key='sample duration',
            value=durations[0],
            styles=styles,
        )
    else:
        toolstr.print_bullet(
            key='sample durations', value=durations, styles=styles
        )
    toolstr.print_bullet(key='extra args', value=vegeta_args, styles=styles)

    if rerun_of is not None:
        toolstr.print_bullet(key='rerun of', value=rerun_of, styles=styles)
    toolstr.print_bullet(
        key='output directory', value=output_dir, styles=styles
    )
    print()


def _print_run_start() -> None:
    import toolstr

    styles = flood.user_io.styles

    print()
    print()
    toolstr.print_header(
        'Running load tests...',
        style=styles['content'],
        text_style=styles['metavar'],
    )
    flood.user_io.print_timestamped('Starting')


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

    styles = flood.user_io.styles

    flood.user_io.print_timestamped('Load tests completed.')

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
        flood.user_io.print_header('Saving results to output directory...')
        toolstr.print_bullet(
            key=os.path.relpath(test_path, output_dir),
            value='',
            colon_str='',
            styles=styles,
        )
        toolstr.print_bullet(
            key=os.path.relpath(result_path, output_dir),
            value='',
            colon_str='',
            styles=styles,
        )
        if figures:
            toolstr.print_bullet(
                key=os.path.relpath(figures_path, output_dir),
                value='',
                colon_str='',
                styles=styles,
            )

    # decide metrics
    if metrics is None:
        metrics = ['success', 'throughput', 'p90']

    # print metrics
    print()
    print()
    flood.user_io.print_header('Summarizing performance metrics...')
    if verbose > 1:
        toolstr.print_bullet(
            key='metrics shown below',
            value=', '.join(metrics),
            styles=styles,
        )
        example_result = list(results.values())[0]
        additional = [
            key for key in example_result.keys() if key not in metrics
        ]
        toolstr.print_bullet(
            key='additional metrics available',
            value=', '.join(additional),
            styles=styles,
        )

    # print metric values
    print()
    flood.user_io.print_metric_tables(
        results=results, metrics=metrics, indent=4
    )

    # deep inspection tables
    if deep_check:
        print()
        print()
        flood.user_io.print_header('Deep inspection of responses...')

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

        print()
        flood.user_io.print_metric_tables(
            results=deep_results_by_category['failed'],
            metrics=['n_invalid_json_errors'],
            indent=4,
        )
        print()
        flood.user_io.print_metric_tables(
            results=deep_results_by_category['failed'],
            metrics=['n_rpc_errors'],
            indent=4,
        )

        metric_names = [
            m for m in metrics if m not in ['success', 'throughput']
        ]
        for (
            category,
            result_category_results,
        ) in deep_results_by_category.items():
            print()
            flood.user_io.print_metric_tables(
                results=result_category_results,
                metrics=metric_names,
                suffix=', ' + category + ' calls',
                indent=4,
            )

