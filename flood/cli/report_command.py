from __future__ import annotations

import typing

import toolcli

import flood


help_message = """create report of previous test results

outputs a notebook file and an html file in output directory"""


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': report_command,
        'help': help_message,
        'args': [
            {
                'name': 'test_dirs',
                'nargs': '+',
                'help': 'space-seperated paths to previous tests',
            },
            {
                'name': ['-o', '--output'],
                'help': 'output directory \[default = current directory]',
            },
            {
                'name': ['-m', '--metrics'],
                'nargs': '+',
                'help': 'metrics to graph in report',
            },
        ],
        'examples': ['tests/test1 tests/test2 tests/test3'],
    }


def report_command(
    test_dirs: typing.Sequence[str],
    output: str | None,
    metrics: typing.Sequence[str] | None,
) -> None:
    if output is None:
        import os

        output = os.getcwd()

    flood.tests.load_tests.create_load_test_report(
        test_paths=test_dirs,
        output_dir=output,
        metrics=metrics,
    )
