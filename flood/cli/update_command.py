from __future__ import annotations

import typing

import toolcli

import flood

help_text = """update flood version

This command only handles the simplest possible use cases of
- pip installs
- git dev installs
    - installed via `flit install --symlink` or `pip install -e ./`

This command cannot:
- switch a pip install to a git dev install
- switch a git dev install to a pip install"""


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': update_command,
        'help': help_text,
        'hidden': True,
        'args': [
            {
                'name': ('--version'),
                'help': 'version to update to',
                'nargs': '?',
            },
            {
                'name': ('--nodes'),
                'help': 'hostnames to update (requires ssh)',
                'nargs': '+',
            },
        ],
    }


def update_command(version: str | None, nodes: typing.Sequence[str]) -> None:
    if nodes is None:
        flood.update_local(version=version)
    else:
        for node in nodes:
            flood.update_remote(hostname=node, version=version)

