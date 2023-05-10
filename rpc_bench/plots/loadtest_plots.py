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
        metrics=['throughput'],
        colors=colors,
        test_name=test_name,
        title='Success Rate vs Request Rate\n(higher is better)',
        ylabel='success rate',
    )
    plt.legend(loc='center right')
    plt.xlim([-0.03, 1.03])


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
    colors: typing.Mapping[str, str] | None = None,
    metrics: typing.Sequence[str] = ['p50', 'p90', 'p99'],
    test_name: str | None = None,
) -> None:
    plot_test_results(
        results=results,
        metrics=metrics,
        colors=colors,
        test_name=test_name,
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
) -> None:
    import matplotlib.pyplot as plt
    import toolplot

    if colors is None:
        colors = {}

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
            plt.plot(
                result['target_rate'],
                result[metric],  # type: ignore
                '.-',
                markersize=20,
                color=color,
                label=name,
                zorder=zorder,
            )

    # set labels
    xlabel = 'requests per second'
    if test_name is not None:
        xlabel += '\n[' + test_name + ']'
    toolplot.set_labels(
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
    )
    plt.legend(loc='center right')

