from __future__ import annotations

import typing

import rpc_bench


#
# # bookkeeping
#


def get_single_test_generators() -> typing.Sequence[str]:
    return [
        item for item in dir(rpc_bench) if item.startswith('generate_test_')
    ]


def get_multi_test_generators() -> typing.Sequence[str]:
    return [
        item for item in dir(rpc_bench) if item.startswith('generate_tests_')
    ]


def get_test_generator(
    test_name: str,
) -> typing.Callable[..., rpc_bench.LoadTest]:
    single_name = 'generate_test_' + test_name
    if hasattr(rpc_bench, single_name):
        return getattr(rpc_bench, single_name)  # type: ignore
    else:
        raise Exception()


def get_test_display_name(test: str) -> str:
    if not test.startswith('generate_test_'):
        raise Exception()
    test = test[len('generate_test_') :]

    head, tail = test.split('_', 1)
    test = head + '_' + snake_case_to_camel_case(tail)

    return test


def get_display_name_test(name: str) -> str:
    raise NotImplementedError()


def snake_case_to_camel_case(string: str) -> str:
    pieces = string.split('_')
    return pieces[0] + ''.join(piece.title() for piece in pieces[1:])


#
# # generation
#


def generate_test(
    test_name: str,
    constants: typing.Mapping[str, typing.Any],
) -> rpc_bench.LoadTest:
    test_generator = get_test_generator(test_name)
    test = test_generator(**constants)
    return test


# def generate_tests(
#     test_name: str,
#     constants: typing.Mapping[str, typing.Any] | None = None,
#     variables: typing.Mapping[
#         str, typing.Mapping[str, typing.Sequence[typing.Any]]
#     ]
#     | None = None,
# ) -> typing.Mapping[str, rpc_bench.LoadTest]:
#     """variables is in format {variable_name: {test_name: variable_value}}"""
#     import itertools

#     if constants is None:
#         constants = {}
#     if variables is None:
#         variables = {}

#     # compute input variables
#     tests_kwargs = []
#     combinations = itertools.product(*variables.items())
#     for combination in combinations:
#         test_kwargs = dict(combination, **constants)
#         tests_kwargs.append(test_kwargs)

#     # use test generator function
#     test_generator = get_test_generator(test_name)
#     tests = []
#     for test_kwargs in tests_kwargs:
#         test = test_generator(**test_kwargs)
#         tests.append(test)

#     return tests

