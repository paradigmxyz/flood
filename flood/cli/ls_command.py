from __future__ import annotations

import toolcli

import flood


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': ls_command,
        'help': 'list available tests',
    }


def ls_command() -> None:
    import toolstr

    toolstr.print_text_box(
        'Available tests',
        text_style=flood.styles['metavar'],
        style=flood.styles['content'],
    )

    print()
    toolstr.print_header(
        'Single Load Tests',
        style=flood.styles['content'],
        text_style=flood.styles['metavar'],
    )
    for test in flood.get_single_test_generators():
        toolstr.print_bullet(key=test, value='', colon_str='')
    print()
    toolstr.print_header(
        'Multi Load Tests',
        style=flood.styles['content'],
        text_style=flood.styles['metavar'],
    )
    toolstr.print_bullet(key='all', value='', colon_str='')
