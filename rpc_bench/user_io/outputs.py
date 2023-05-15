from __future__ import annotations

import typing

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

