from __future__ import annotations

import typing

import rpc_bench
from rpc_bench import spec

if typing.TYPE_CHECKING:
    import types

    import polars as pl
    import toolcli


styles: toolcli.StyleTheme = {
    'title': 'bold #00e100',
    'metavar': 'bold #e5e9f0',
    'description': '#aaaaaa',
    'content': '#00B400',
    'option': 'bold #e5e9f0',
    'comment': '#888888',
}


colors = {
    'orange_shades': [
        'darkgoldenrod',
        'darkorange',
        'gold',
    ],
    'blue_shades': [
        'blue',
        'dodgerblue',
        'lightskyblue',
    ],
    'streetlight': [
        'crimson',
        'goldenrod',
        'limegreen',
    ],
}

color_defaults = [
    'darkorange',
    'dodgerblue',
]


def _get_tqdm() -> types.ModuleType:
    import sys

    if 'jupyter_client' in sys.modules:
        try:
            import ipywidgets  # type: ignore
            import tqdm.notebook as tqdm

            return tqdm
        except ImportError:
            pass

    import tqdm  # type: ignore

    return tqdm


def outputs_to_dataframe(
    outputs: typing.Mapping[str, spec.LoadTestOutput]
) -> pl.DataFrame:
    import polars as pl

    return pl.concat(
        [
            pl.DataFrame(data).with_columns(pl.lit(name).alias('test'))
            for name, data in outputs.items()
        ]
    )


def print_metric_tables(
    results: typing.Mapping[str, spec.LoadTestOutput],
    metrics: typing.Sequence[str],
) -> None:
    import toolstr

    if len(results) == 0:
        print('no results')
        print()

    names = list(results.keys())
    rates = results[names[0]]['target_rate']
    for metric in metrics:
        if metric == 'success':
            suffix = ''
        else:
            suffix = ' (s)'
        unitted_names = [name + suffix for name in names]
        labels = ['rate (rps)'] + unitted_names
        toolstr.print_text_box(
            toolstr.add_style(metric + ' vs load', rpc_bench.styles['metavar']),
            style=rpc_bench.styles['content'],
        )

        rows = [[rate] for rate in rates]
        for name, result in results.items():
            for row, value in zip(rows, result[metric]):  # type: ignore
                row.append(value)
        column_formats = {name: {'decimals': 3} for name in names}
        toolstr.print_table(
            rows,
            labels=labels,
            column_formats=column_formats,  # type: ignore
            label_style=rpc_bench.styles['metavar'],
            border=rpc_bench.styles['content'],
        )
        if metric != metrics[-1]:
            print()

