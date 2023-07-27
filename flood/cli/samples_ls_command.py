from __future__ import annotations

import os
import toolcli
import toolstr

import flood


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': samples_ls_command,
        'help': 'list raw EVM data samples that are downloaded and downloadable',  # noqa: E501
        'args': [],
    }


def samples_ls_command() -> None:
    version = 'v1_0_0'

    # parse contents of flood samples dir
    samples_dir = flood.generators.get_flood_samples_dir()
    files_by_network: dict[str, list[str]] = {}
    for filename in os.listdir(samples_dir):
        if filename.endswith('parquet'):
            network = filename.split('_')[0]
            files_by_network.setdefault(network, [])
            files_by_network[network].append(filename)
    for network in list(files_by_network.keys()):
        files_by_network[network] = sorted(files_by_network[network])

    for network in files_by_network.keys():
        toolstr.print_text_box(network + ' sample data')
        print()
        print(samples_dir)
        print()
        toolstr.print_header('Local Files')
        for filename in files_by_network[network]:
            print('-', filename)

        missing = []
        for size in flood.generators.default_sizes:
            for datatype in flood.generators.default_datatypes:
                filename = flood.generators.raw_data_file_template.format(
                    network=network,
                    size=size,
                    datatype=datatype,
                    version=version,
                )
                if filename not in files_by_network[network]:
                    missing.append(filename)

        if len(missing) > 0:
            print()
            toolstr.print_header('Available for download')
            for filename in missing:
                print('-', filename)
            print()
            print('download using `flood samples download` command')
