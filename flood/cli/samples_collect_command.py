from __future__ import annotations

import typing

import toolcli

import flood


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': samples_collect_command,
        'help': 'collect raw EVM samples using Paradigm Data Portal datasets',
        'args': [
            {
                'name': ('-n', '--network'),
                'help': 'network, default ethereum',
            },
            {
                'name': ('-s', '--sizes'),
                'help': 'sample sizes of {XS, S, M, L, XL}, default all',
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


def samples_collect_command(
    network: str | None,
    sizes: typing.Sequence[str] | None,
    output_dir: str | None,
    datatypes: typing.Sequence[str] | None,
) -> None:
    if output_dir is None:
        output_dir = flood.generators.get_flood_samples_dir()
    if network is None:
        network = 'ethereum'
    flood.generators.create_samples_dataset(
        output_dir=output_dir,
        network=network,
        sizes=sizes,
        datatypes=datatypes,
    )
