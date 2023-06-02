from __future__ import annotations

import toolcli


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': samples_ls_command,
        'help': 'list raw EVM data samples that are downloaded and downloadable',
        'args': [
        ],
    }


def samples_ls_command() -> None:
    raise NotImplementedError()

