from __future__ import annotations

import toolcli

import flood


def run_cli(raw_command: str | None = None) -> None:
    command_index: toolcli.CommandIndex = {
        (): 'flood.cli.root_command',
        ('ls',): 'flood.cli.ls_command',
        ('report',): 'flood.cli.report_command',
        (
            'version',
        ): 'toolcli.command_utils.standard_subcommands.version_command',
        ('help',): 'toolcli.command_utils.standard_subcommands.help_command',
    }

    config: toolcli.CLIConfig = {
        'base_command': 'flood',
        'description': flood.__doc__,
        'version': flood.__version__,
        'default_command_sequence': (),
        'root_help_arguments': True,
        # 'root_help_subcommands': False,
        'include_debug_arg': True,
        'style_theme': flood.styles,
    }

    toolcli.run_cli(
        command_index=command_index,
        config=config,
    )

