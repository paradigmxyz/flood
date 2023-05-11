from __future__ import annotations

import typing

import rpc_bench


def plot_success(
    results: typing.Mapping[str, rpc_bench.LoadTestOutput],
    colors: typing.Mapping[str, str] | None = None,
    test_name: str | None = None,
) -> None:
    import matplotlib.pyplot as plt  # type: ignore

    plot_test_results(
        results=results,
        metrics=['success'],
        colors=colors,
        test_name=test_name,
        title='Success Rate vs Request Rate\n(higher is better)',
        ylabel='success rate',
        ylim=[-0.03, 1.03],
    )
    plt.legend(loc='center right')


def plot_throughput(
    results: typing.Mapping[str, rpc_bench.LoadTestOutput],
    colors: typing.Mapping[str, str] | None = None,
    test_name: str | None = None,
) -> None:
    plot_test_results(
        results=results,
        metrics=['throughput'],
        colors=colors,
        test_name=test_name,
        title='Throughput vs Request Rate\n(higher is better)',
        ylabel='throughput\n(responses per second)',
    )


def plot_latencies(
    results: typing.Mapping[str, rpc_bench.LoadTestOutput],
    colors: typing.Mapping[
        str,
        str | typing.Sequence[str] | typing.Mapping[str, str],
    ]
    | None = None,
    metrics: typing.Sequence[str] = ['p99', 'p90', 'p50'],
    test_name: str | None = None,
) -> None:
    if colors is None:
        colors = dict(zip(results.keys(), rpc_bench.colors.values()))

    plot_test_results(
        results=results,
        metrics=metrics,
        colors=colors,
        test_name=test_name,
        ymin=0,
        title='Latency vs Request Rate\n(lower is better)',
        ylabel='latency (seconds)',
    )


def plot_test_results(
    results: typing.Mapping[str, rpc_bench.LoadTestOutput],
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
) -> None:
    import matplotlib.pyplot as plt
    import toolplot

    if colors is None:
        colors = {
            key: color
            for key, color in zip(results.keys(), rpc_bench.color_defaults)
        }

    for name, result in results.items():
        # determine colors
        result_colors = colors.get(name)
        if isinstance(result_colors, str):
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

