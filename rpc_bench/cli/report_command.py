from __future__ import annotations

import toolcli


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': report_command,
        'help': 'output summary of previous test results',
        'args': [
            {
                'name': 'previous_output_path',
                'help': 'path to output of previous test',
            },
        ],
    }


def report_command(previous_output_path: str) -> None:
    print(previous_output_path)

