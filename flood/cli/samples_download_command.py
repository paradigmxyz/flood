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
                'name': ('-s', '--size'),
                'help': 'sample size, one of {XS, S, M, L, XL}, default L',
            },
            {
                'name': ('-o', '--output-dir'),
                'help': 'download location, default FLOOD_SAMPLES_DIR or cwd',
            },
            {
                'name': ('-d', '--datatypes'),
                'help': 'datatypes to sample, default all',
            },
        ],
    }


def download_samples_command(
    network: str | None,
    size: str | None,
    output_dir: str | None,
    datatypes: typing.Sequence[str] | None,
) -> None:
    if network is None:
        network = 'ethereum'
    if size is None:
        size = 'L'
    if output_dir is None:
        output_dir = flood.get_flood_samples_dir()

    flood.download_samples(
        network=network,
        size=size,
        datatypes=datatypes,
        output_dir=output_dir,
    )

