from __future__ import annotations

import typing

import flood


_path_templates = {
    'multi_indicator': 'multi_test.fyi',
}


def _save_multi_run_tests(
    output_dir: str,
    tests: typing.Mapping[str, flood.LoadTest],
) -> None:
    raise NotImplementedError()
    # import os

    # # make output dir
    # if not os.path.isdir(output_dir):
    #     if os.path.exists(output_dir):
    #         raise Exception('output must be a directory path')
    #     else:
    #         os.makedirs(output_dir, exist_ok=True)

    # # create individual tests
    # for test_name, test in tests.items():
    #     single_runner_io._save_single_run_test(
    #         test_name=test_name,
    #         output_dir=os.path.join(output_dir, test_name),
    #         test=test,
    #     )

    # # create multitest indicator file
    # indicator_path = os.path.join(
    #     output_dir, _path_templates['multi_indicator']
    # )
    # with open(indicator_path, 'a'):
    #     pass


def _load_multi_run_tests(
    output_dir: str,
) -> typing.Mapping[str, flood.LoadTest]:
    raise NotImplementedError()

