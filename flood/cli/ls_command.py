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

    styles = flood.user_io.styles

    toolstr.print_text_box(
        'Available tests',
        text_style=styles['metavar'],
        style=styles['content'],
    )

    print()
    toolstr.print_header(
        'Single Load Tests',
        style=styles['content'],
        text_style=styles['metavar'],
    )
    for test in flood.generators.get_single_test_generators():
        toolstr.print_bullet(key=test, value='', colon_str='')
    print()
    toolstr.print_header(
        'Multi Load Tests',
        style=styles['content'],
        text_style=styles['metavar'],
    )
    toolstr.print_bullet(key='all', value='', colon_str='')
