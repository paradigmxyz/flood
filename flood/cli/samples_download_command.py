from __future__ import annotations

import typing

import toolcli

import flood


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': download_samples_command,
        'help': 'download raw EVM samples for constructing calls',
        'args': [
            {
                'name': ('-n', '--network'),
                'help': 'network, default ethereum',
            },
            {
                'name': ('-s', '--sizes'),
                'help': 'sample sizes, one of {XS, S, M, L, XL, all}, default L',  # noqa: E501
                'nargs': '+',
            },
            {
                'name': ('-o', '--output-dir'),
                'help': 'download location, default FLOOD_SAMPLES_DIR or cwd',
            },
            {
                'name': ('-d', '--datatypes'),
                'help': 'datatypes to sample, default all',
            },
            {
                'name': ('-m', '--missing'),
                'help': 'only download missing files',
                'action': 'store_true',
            },
        ],
    }


def download_samples_command(
    network: str | None,
    sizes: typing.Sequence[str] | None,
    output_dir: str | None,
    datatypes: typing.Sequence[str] | None,
    missing: bool,
) -> None:
    if network is None:
        network = 'ethereum'
    if sizes is None:
        sizes = ['L']
    if sizes == 'all':
        sizes = list(flood.generators.default_sizes.keys())
    if output_dir is None:
        output_dir = flood.generators.get_flood_samples_dir()

    flood.generators.download_raw_data(
        network=network,
        sizes=sizes,
        datatypes=datatypes,
        output_dir=output_dir,
        only_missing=missing,
    )
