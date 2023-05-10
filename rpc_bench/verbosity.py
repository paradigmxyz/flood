from __future__ import annotations

import typing

from . import spec

if typing.TYPE_CHECKING:
    import datetime
    import types


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


def _print_benchmark_prelude(
    *,
    nodes: typing.Mapping[str, spec.Node],
    methods: typing.Sequence[str] | None,
    samples: int | None,
    random_seed: int | str | None,
    calls: spec.MethodCalls,
    output_file: str | None = None,
    start_time: datetime.datetime,
) -> None:
    import toolstr

    toolstr.print_text_box(
        toolstr.add_style('RPC Benchmark', spec.styles['metavar']),
        style=spec.styles['content'],
        double=True,
    )

    if len(nodes) == 1:
        node = list(nodes.values())[0]
        name = node['name']
        url = node['url']
        if name == url:
            label = url
        else:
            label = name + ' (' + url + ')'
        toolstr.print_bullet(key='node', value=label, styles=spec.styles)
    elif len(nodes) > 1:
        toolstr.print_bullet(key='nodes', value='', styles=spec.styles)
        for node in nodes.values():
            name = node['name']
            url = node['url']
            if name == url:
                label = name
            else:
                label = name + ' (' + url + ')'
            toolstr.print_bullet(
                key=label,
                value='',
                colon_str='',
                indent=4,
                styles=spec.styles,
                key_style=spec.styles['description'],
            )
    else:
        raise Exception('no nodes specified')

    if methods is None:
        methods = sorted(list(calls.keys()))
    toolstr.print_bullet(
        key='methods', value=', '.join(methods), styles=spec.styles
    )

    if samples is None:
        example_calls = next(iter(calls.values()))
        samples = len(example_calls)
    toolstr.print_bullet(key='samples', value=samples, styles=spec.styles)

    if random_seed is None:
        random_seed = 'not specified'
    toolstr.print_bullet(
        key='random_seed', value=random_seed, styles=spec.styles
    )
    toolstr.print_bullet(
        key='output_file', value=output_file, styles=spec.styles
    )
    toolstr.print_bullet(
        key='start_time',
        value=start_time,
        styles=spec.styles,
    )


def _print_benchmark_summary(
    latencies: spec.NodesMethodLatencies,
    start_time: datetime.datetime,
    calls: spec.MethodCalls,
) -> None:
    import datetime
    import time
    import numpy as np
    import toolstr

    print()
    print()
    toolstr.print_header(
        toolstr.add_style(
            'Benchmark Summary', spec.styles['metavar']
        ),
        style=spec.styles['content'],
    )
    end_time = datetime.datetime.fromtimestamp(int(time.time()))
    toolstr.print_bullet(
        key='start_time',
        value=start_time,
        styles=spec.styles,
    )
    toolstr.print_bullet(
        key='end_time',
        value='  ' + str(end_time),
        styles=spec.styles,
    )
    toolstr.print_bullet(
        key='duration',
        value='  ' + str(end_time - start_time).split('.')[0],
        styles=spec.styles,
    )

    # print table of latency per provider
    all_latencies: list[float] = []
    rows = []
    for method in calls.keys():
        row = [method]
        for node in latencies.keys():
            array = np.array(latencies[node][method])
            all_latencies.extend(latencies[node][method])
            row.append(array.mean())

        if len(latencies.keys()) == 2:
            row.append(row[1] / row[2])  # type: ignore
        rows.append(row)

    print()
    print()
    toolstr.print_text_box(
        toolstr.add_style('Mean Latencies (seconds)', spec.styles['metavar']),
        style=spec.styles['content'],
    )

    node_names = list(latencies.keys())
    labels = ['method'] + node_names
    if len(latencies) == 2:
        labels.append(node_names[0] + ' / ' + node_names[1])

    if any(latency < 0.001 for latency in all_latencies):
        decimals = 4
    else:
        decimals = 3

    toolstr.print_table(
        rows,
        indent=4,
        labels=labels,
        border=spec.styles['content'],
        label_style=spec.styles['metavar'],
        column_styles={'method': spec.styles['metavar']},
        column_formats={name: {'decimals': decimals} for name in node_names},
    )


def _print_local_execution_prelude() -> None:
    import toolstr

    print()
    print()
    toolstr.print_header(
        toolstr.add_style('Performing Local Benchmarks...', spec.styles['metavar']),
        style=spec.styles['content'],
    )


def _print_local_execution_summary() -> None:
    pass


def _get_progress_bars(
    nodes: typing.Mapping[str, spec.Node],
    verbose: bool,
) -> tuple[spec.ProgressBar, spec.ProgressBar, spec.ProgressBar]:
    if len(nodes) == 1:
        positions = [None, 0, 1]
    else:
        positions = [0, 1, 2]
    node_bar: spec.ProgressBar = {
        'desc': '  nodes',
        'position': positions[0],
        'leave': True,
        'colour': spec.styles['content'],
        'disable': (not verbose) or (len(nodes) == 1),
    }
    method_bar: spec.ProgressBar = {
        'desc': 'methods',
        'position': positions[1],
        'leave': len(nodes) == 1,
        'colour': spec.styles['content'],
        'disable': not verbose,
    }
    sample_bar: spec.ProgressBar = {
        'desc': 'samples',
        'position': positions[2],
        'leave': False,
        'colour': spec.styles['content'],
        'disable': not verbose,
    }
    return node_bar, method_bar, sample_bar

