from __future__ import annotations

import typing

import flood


def plot_load_test_results(
    outputs: typing.Mapping[str, flood.LoadTestOutput],
    test_name: str,
    output_dir: str | None = None,
    latency_yscale_log: bool = True,
    colors: typing.Mapping[str, str] | None = None,
    title_suffix: str | None = None,
    file_suffix: str | None = None,
    plot_success_rate: bool = True,
    plot_throughput: bool = True,
    plot_latency: bool = True,
) -> None:
    import os
    import matplotlib.pyplot as plt  # type: ignore
    import toolplot

    if title_suffix is None:
        title_suffix = ''
    if file_suffix is None:
        file_suffix = ''

    toolplot.setup_plot_formatting()

    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)

    if plot_success_rate:
        plt.figure()
        plot_load_test_success(outputs, test_name=test_name, colors=colors)
        if output_dir is not None:
            path = os.path.join(
                output_dir, 'success_rate' + file_suffix + '.png'
            )
            plt.savefig(path)
        else:
            plt.show()

    if plot_throughput:
        plt.figure()
        plot_load_test_throughput(outputs, test_name=test_name, colors=colors)
        if output_dir is not None:
            path = os.path.join(output_dir, 'throughput' + file_suffix + '.png')
            plt.savefig(path)
        else:
            plt.show()

    if plot_latency:
        plt.figure()
        plot_load_test_latencies(
            outputs,
            test_name=test_name,
            yscale_log=latency_yscale_log,
            colors=colors,
        )
        if output_dir is not None:
            path = os.path.join(output_dir, 'latencies' + file_suffix + '.png')
            plt.savefig(path)
        else:
            plt.show()

    # deep graphs
    example_output = next(iter(outputs.values()))
    if (
        example_output.get('raw_output') is not None
        and example_output['raw_output'][0] is not None
    ):
        import polars as pl

        dfs = flood.load_single_run_raw_output(
            results=outputs,
            sample_index=list(range(len(example_output['raw_output']))),
        )
        success_dfs = {
            name: df.filter(pl.col('status_code') == 200)
            for name, df in dfs.items()
        }
        fail_dfs = {
            name: df.filter(pl.col('status_code') != 200)
            for name, df in dfs.items()
        }
        success_deep_outputs = flood.compute_raw_output_metrics(
            raw_output=success_dfs, results=outputs
        )
        fail_deep_outputs = flood.compute_raw_output_metrics(
            raw_output=fail_dfs, results=outputs
        )
        plot_load_test_results(
            outputs=success_deep_outputs,
            test_name=test_name,
            title_suffix=', successful calls only',
            file_suffix='_successful_calls',
            plot_success_rate=False,
            plot_throughput=False,
            output_dir=output_dir,
            latency_yscale_log=latency_yscale_log,
            colors=colors,
        )
        plot_load_test_results(
            outputs=fail_deep_outputs,
            test_name='failed ' + test_name,
            title_suffix=', failed calls only',
            file_suffix='_failed_calls',
            plot_success_rate=False,
            plot_throughput=False,
            output_dir=output_dir,
            latency_yscale_log=latency_yscale_log,
            colors=colors,
        )


def plot_load_test_success(
    results: typing.Mapping[str, flood.LoadTestOutput],
    colors: typing.Mapping[str, str] | None = None,
    test_name: str | None = None,
) -> None:
    import matplotlib.pyplot as plt

    plot_load_test_result_metrics(
        results=results,
        metrics=['success'],
        colors=colors,
        test_name=test_name,
        title='Success Rate vs Request Rate\n(higher is better)',
        ylabel='success rate',
        ylim=[-0.03, 1.03],
    )
    plt.legend(loc='center right')


def plot_load_test_throughput(
    results: typing.Mapping[str, flood.LoadTestOutput],
    colors: typing.Mapping[str, str] | None = None,
    test_name: str | None = None,
) -> None:
    import matplotlib.pyplot as plt

    plot_load_test_result_metrics(
        results=results,
        metrics=['throughput'],
        colors=colors,
        test_name=test_name,
        title='Throughput vs Request Rate\n(higher is better)',
        ylabel='throughput\n(responses per second)',
        ymin=0,
    )
    plt.legend(loc='upper left')


def plot_load_test_latencies(
    results: typing.Mapping[str, flood.LoadTestOutput],
    colors: typing.Mapping[
        str,
        str | typing.Sequence[str] | typing.Mapping[str, str],
    ]
    | None = None,
    metrics: typing.Sequence[str] = ['p99', 'p90', 'p50'],
    test_name: str | None = None,
    yscale_log: bool = False,
) -> None:
    import matplotlib.pyplot as plt

    if colors is None:
        colors = dict(zip(results.keys(), flood.plot_colors.values()))

    if yscale_log:
        ymin = None
    else:
        ymin = 0

    plot_load_test_result_metrics(
        results=results,
        metrics=metrics,
        colors=colors,
        test_name=test_name,
        ymin=ymin,
        title='Latency vs Request Rate\n(lower is better)',
        ylabel='latency (seconds)',
        yscale_log=yscale_log,
    )
    plt.legend(loc='upper left')


def plot_load_test_result_metrics(
    results: typing.Mapping[str, flood.LoadTestOutput],
    metrics: typing.Sequence[str],
    *,
    colors: typing.Mapping[
        str,
        str | typing.Sequence[str] | typing.Mapping[str, str],
    ]
    | None = None,
    test_name: str | None = None,
    title: str | None = None,
    ylabel: str | None = None,
    ylim: typing.Sequence[float] | None = None,
    ymin: float | int | None = None,
    yscale_log: bool = False,
) -> None:
    import matplotlib.pyplot as plt
    import toolplot

    if colors is None:
        colors = {
            key: color for key, color in zip(results.keys(), flood.plot_colors)
        }

    for name, result in results.items():
        # determine colors
        result_colors = colors.get(name)
        if isinstance(result_colors, str):
            if result_colors in flood.plot_colors:
                if len(metrics) == 1:
                    result_colors = [flood.plot_colors[result_colors][1]]
                else:
                    result_colors = flood.plot_colors[result_colors]
            else:
                result_colors = [result_colors] * len(metrics)
        elif isinstance(result_colors, list):
            assert len(result_colors) >= len(metrics), 'not enough colors'
        elif isinstance(result_colors, dict):
            for metric in metrics:
                assert metric in result_colors, 'missing color for ' + metric
            result_colors = [result_colors[metric] for metric in metrics]
        else:
            raise Exception('invalid color format')

        # plot
        for zorder, metric, color in zip(
            range(len(metrics)), metrics, result_colors
        ):
            label = name
            if len(metrics) > 1:
                label += ' ' + metric
            plt.plot(
                result['target_rate'],
                result[metric],  # type: ignore
                '.-',
                markersize=20,
                color=color,
                label=label,
                zorder=zorder,
            )

    # set labels
    if yscale_log:
        plt.yscale('log')
    if ylim is not None:
        plt.ylim(*ylim)
    if ymin is not None:
        ylim = plt.ylim()
        plt.ylim([ymin, ylim[1]])  # type: ignore
    xlabel = 'requests per second'
    if test_name is not None:
        xlabel += '\n[' + test_name + ']'
    toolplot.set_labels(
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
    )
    plt.legend(loc='center right')

