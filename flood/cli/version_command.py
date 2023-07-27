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
            {
                'name': '--json',
                'help': 'output version details as json',
                'action': 'store_true',
                'dest': 'as_json',
            },
            {'name': ('-V', '--version'), 'action': 'store_true'},
        ],
    }


def version_command(node_url: str | None, as_json: bool, version: bool) -> None:
    if node_url is None:
        installation = flood.get_local_installation()
    else:
        installation = flood.get_remote_installation(node_url)

    if as_json:
        import json

        print(json.dumps(installation, indent=4, sort_keys=True))
    else:
        print(installation['flood_version'])

