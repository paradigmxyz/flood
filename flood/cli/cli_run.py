from __future__ import annotations

import toolcli

import flood

cd_dir_help = {
    'samples': 'FLOOD_SAMPLES_PATH env value',
}


def cd_dir_getter(dirname: str) -> str:
    if dirname == 'samples':
        return flood.generators.get_flood_samples_dir()
    else:
        raise Exception('unknown path: ' + str(dirname))


def run_cli(raw_command: str | None = None) -> None:
    command_index: toolcli.CommandIndex = {
        (): 'flood.cli.root_command',
        ('help',): 'toolcli.command_utils.standard_subcommands.help_command',
        ('ls',): 'flood.cli.ls_command',
        ('print',): 'flood.cli.print_command',
        ('report',): 'flood.cli.report_command',
        ('samples', 'collect'): 'flood.cli.samples_collect_command',
        ('samples', 'download'): 'flood.cli.samples_download_command',
        ('samples', 'ls'): 'flood.cli.samples_ls_command',
        ('version',): 'flood.cli.version_command',
        ('cd',): 'toolcli.command_utils.standard_subcommands.cd_command',
        ('update',): 'flood.cli.update_command',
    }

    config: toolcli.CLIConfig = {
        'base_command': 'flood',
        'description': flood.__doc__,
        'version': flood.__version__,
        'default_command_sequence': (),
        'root_help_arguments': True,
        # 'root_help_subcommands': False,
        'include_debug_arg': True,
        'style_theme': flood.user_io.styles,
        'cd_dir_help': cd_dir_help,
        'cd_dir_getter': cd_dir_getter,
    }

    toolcli.run_cli(
        command_index=command_index,
        config=config,
    )
