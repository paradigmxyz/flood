from __future__ import annotations

import typing

import rpc_bench


def get_available_tests() -> typing.Sequence[str]:
    return [
        item
        for item in dir(rpc_bench)
        if item.startswith('generate_tests_')
    ]


def get_test_display_name(test: str) -> str:
    if not test.startswith('generate_tests_'):
        raise Exception()
    test = test[len('generate_tests_'):]
    return test


def get_display_name_test(name: str) -> str:
    pass


# def generate_tests(
#     constants: typing.Mapping[str, typing.Any],
#     variables: typing.Mapping[str, typing.Sequence[typing.Any]],
# ) -> typing.Mapping[str, rpc_bench.LoadTest]:
#     import itertools

#     all_keys = set()

#     pre_tests = []
#     combinations = itertools.product(*variables.items())
#     for combination in combinations:
#         pre_test = dict(combination, **constants)
#         pre_tests.append(pre_test)



