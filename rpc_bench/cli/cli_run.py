from __future__ import annotations

import toolcli

import rpc_bench


def run_cli(raw_command: str | None = None) -> None:
    command_index: toolcli.CommandIndex = {
        (): 'rpc_bench.cli.root_command',
        (
            'version',
        ): 'toolcli.command_utils.standard_subcommands.version_command',
        ('help',): 'toolcli.command_utils.standard_subcommands.help_command',
    }

    config: toolcli.CLIConfig = {
        'base_command': 'rpc_bench',
        'description': rpc_bench.__doc__,
        'version': rpc_bench.__version__,
        'default_command_sequence': (),
        'root_help_arguments': True,
        'root_help_subcommands': False,
        'include_debug_arg': True,
        'style_theme': rpc_bench.styles,
    }

    toolcli.run_cli(
        command_index=command_index,
        config=config,
    )

