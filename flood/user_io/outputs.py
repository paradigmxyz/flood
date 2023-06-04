from __future__ import annotations

import typing

import flood
from flood import spec

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


plot_colors = {
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


def print_load_test_summary(test: flood.LoadTest) -> None:
    import toolstr

    parsed = flood.parse_test_data(test)
    rates = parsed['rates']
    durations = parsed['durations']
    vegeta_kwargs = parsed['vegeta_kwargs']

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


def print_metric_tables(
    results: typing.Mapping[str, spec.LoadTestOutput],
    metrics: typing.Sequence[str],
    *,
    decimals: int | None = None,
    comparison: bool = False,
    indent: int | str | None = None,
) -> None:
    import toolstr

    if len(results) == 0:
        toolstr.print('no results', indent=indent)
        print()

    names = list(results.keys())
    rates = results[names[0]]['target_rate']
    for metric in metrics:
        # create labels
        if metric == 'success':
            suffix = ''
        else:
            suffix = ' (s)'
        unitted_names = [name + suffix for name in names]
        labels = ['rate (rps)'] + unitted_names
        if comparison:
            if len(results) != 2:
                raise NotImplementedError('comparison of >2 tests')
            comparison_label = names[0] + ' / ' + names[1]
            labels.append(comparison_label)
        else:
            comparison_label = None

        # build rows
        rows: list[list[typing.Any]] = [[rate] for rate in rates]
        values = []
        for name, result in results.items():
            for row, value in zip(rows, result[metric]):  # type: ignore
                row.append(value)
                values.append(value)
        if comparison:
            for row in rows:
                row.append(row[-2] / row[-1])

        # compute column formats
        if all(value > 1 for value in values):
            use_decimals = 1
        else:
            if decimals is None:
                use_decimals = 6
            else:
                use_decimals = decimals
        column_formats = {
            column: {'decimals': use_decimals} for column in unitted_names
        }
        if comparison_label is not None:
            column_formats[comparison_label] = {
                'decimals': 1,
                'percentage': True,
            }

        # print header
        toolstr.print_text_box(
            toolstr.add_style(metric + ' vs load', flood.styles.get('metavar')),
            style=flood.styles.get('content'),
            indent=indent,
        )

        # print table
        toolstr.print_table(
            rows,
            labels=labels,
            column_formats=column_formats,  # type: ignore
            label_style=flood.styles.get('metavar'),
            border=flood.styles.get('content'),
            indent=indent,
        )
        if metric != metrics[-1]:
            print()


#
# # generic restylings of toolstr functions
#


def print_text_box(text: str) -> None:
    import toolstr

    toolstr.print_text_box(
        text,
        text_style=flood.styles.get('metavar'),
        style=flood.styles.get('content'),
    )


def print_header(text: str) -> None:
    import toolstr

    toolstr.print_header(
        text,
        text_style=flood.styles.get('metavar'),
        style=flood.styles.get('content'),
    )


def print_bullet(*args: typing.Any, **kwargs: typing.Any) -> None:
    import toolstr

    toolstr.print_bullet(
        *args,
        **kwargs,
        styles=flood.styles,
    )


def print_table(*args: typing.Any, **kwargs: typing.Any) -> None:
    import toolstr

    toolstr.print_table(
        *args,
        **kwargs,
        label_style=flood.styles.get('metavar'),
        border=flood.styles.get('content'),
    )


def print_multiline_table(*args: typing.Any, **kwargs: typing.Any) -> None:
    import toolstr

    toolstr.print_multiline_table(
        *args,
        **kwargs,
        label_style=flood.styles.get('metavar'),
        border=flood.styles.get('content'),
    )

