from __future__ import annotations

import typing

import flood
from flood import spec

if typing.TYPE_CHECKING:
    import types

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
    'green_shades': [
        'forestgreen',
        'limegreen',
        'chartreuse',
    ],
    'red_shades': [
        'firebrick',
        'red',
        'salmon',
    ],
    'purple_shades': [
        'rebeccapurple',
        'blueviolet',
        'mediumslateblue',
    ],
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


def get_nodes_plot_colors(
    nodes: typing.Mapping[str, flood.Node]
) -> typing.Mapping[str, str]:
    colors = {}
    taken = set()
    for node in nodes.values():
        # print version
        version = node['client_version']
        if version is None:
            version = ''

        # decide color
        if (
            (version is not None and 'reth' in version)
            or ('reth' in node['name'])
        ) and 'orange_shades' not in taken:
            color = 'orange_shades'
        elif (
            (version is not None and 'erigon' in version)
            or ('erigon' in node['name'])
        ) and 'blue_shades' not in taken:
            color = 'blue_shades'
        else:
            for color_name in plot_colors.keys():
                if color_name not in taken:
                    color = color_name
                    break
            else:
                raise Exception('out of colors')

        colors[node['name']] = color
        taken.add(color)

    return colors


def _get_tqdm() -> types.ModuleType:
    import sys

    if 'jupyter_client' in sys.modules:
        try:
            import ipywidgets  # type: ignore # noqa: F401
            import tqdm.notebook as tqdm

            return tqdm
        except ImportError:
            pass

    import tqdm  # type: ignore

    return tqdm


def print_metric_tables(
    results: typing.Mapping[str, spec.LoadTestOutput | spec.LoadTestDeepOutput],
    metrics: typing.Sequence[str],
    *,
    suffix: str = '',
    decimals: int | None = None,
    comparison: bool | None = None,
    indent: int | str | None = None,
) -> None:
    import toolstr

    if len(results) == 0:
        toolstr.print('no results', indent=indent)
        print()
    if comparison is None:
        comparison = len(results) == 2

    names = list(results.keys())
    rates = results[names[0]]['target_rate']
    for metric in metrics:
        # create labels
        if metric in ['success', 'n_invalid_json_errors', 'n_rpc_errors']:
            metric_suffix = ''
        elif metric == 'throughput':
            metric_suffix = ' (rps)'
        else:
            metric_suffix = ' (s)'
        unitted_names = [name + metric_suffix for name in names]
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
        if all(value > 1 for value in values if value is not None):
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
            toolstr.add_style(
                metric + ' vs load' + suffix, styles.get('metavar')
            ),
            style=styles.get('content'),
            indent=indent,
        )

        if metric == 'success':
            for label in labels[1:]:
                column_formats.setdefault(label, {})
                column_formats[label]['percentage'] = True
                column_formats[label]['decimals'] = 1

        # print table
        toolstr.print_table(
            rows,
            labels=labels,
            column_formats=column_formats,  # type: ignore
            label_style=styles.get('metavar'),
            border=styles.get('content'),
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
        text_style=styles.get('metavar'),
        style=styles.get('content'),
    )


def print_header(text: str) -> None:
    import toolstr

    toolstr.print_header(
        text,
        text_style=styles.get('metavar'),
        style=styles.get('content'),
    )


def print_bullet(*args: typing.Any, **kwargs: typing.Any) -> None:
    import toolstr

    toolstr.print_bullet(
        *args,
        **kwargs,
        styles=styles,
    )


def print_table(*args: typing.Any, **kwargs: typing.Any) -> None:
    import toolstr

    toolstr.print_table(
        *args,
        **kwargs,
        label_style=styles.get('metavar'),
        border=styles.get('content'),
    )


def print_multiline_table(*args: typing.Any, **kwargs: typing.Any) -> None:
    import toolstr

    toolstr.print_multiline_table(
        *args,
        **kwargs,
        label_style=styles.get('metavar'),
        border=styles.get('content'),
    )


def print_timestamped(message: str) -> None:
    import datetime
    import toolstr

    dt = datetime.datetime.now()
    if dt.microsecond >= 500_000:
        dt = dt + datetime.timedelta(microseconds=1_000_000 - dt.microsecond)
    else:
        dt = dt - datetime.timedelta(microseconds=dt.microsecond)
    timestamp = (
        toolstr.add_style('\[', styles['content'])
        + toolstr.add_style(str(dt), styles['metavar'])
        + toolstr.add_style(']', styles['content'])
    )
    toolstr.print(timestamp + ' ' + message)


def disable_text_colors() -> None:
    for key in list(styles.keys()):
        del styles[key]  # type: ignore

