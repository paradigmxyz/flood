from __future__ import annotations

import toolcli

import rpc_bench


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': ls_command,
        'help': 'list available tests',
    }


def ls_command() -> None:
    print('Available tests:')
    for test in rpc_bench.get_available_tests():
        print('-', rpc_bench.get_test_display_name(test))

