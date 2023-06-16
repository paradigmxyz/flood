from __future__ import annotations

import typing

import flood
from . import single_runner_io


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
    flood.print_metric_tables(
        results=results,
        metrics=metrics,
        indent=4,
    )

