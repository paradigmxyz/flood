from __future__ import annotations

import toolcli

import flood


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': version_command,
        'help': 'get flood version of local or remote installation',
        'args': [
            {
                'name': 'node_url',
                'help': 'remote node url, if none use local installation',
                'nargs': '?',
            },
        ],
    }


def version_command(node_url: str | None) -> None:
    if node_url is None:
        installation = flood.get_local_installation()
    else:
        installation = flood.get_remote_installation(node_url)
    print(installation['flood_version'])

