from __future__ import annotations

import typing

import rpc_bench

# def create_loadtests(
#     url: str | None = None,
#     urls: typing.Sequence[str] | None = None,
#     calls: typing.Sequence[spec.Call] | None = None,
#     calls_lists: typing.Sequence[typing.Sequence[spec.Call]] | None = None,
#     duration: int | None = None,
#     durations: typing.Sequence[int] | typing.Mapping[str, int] | None = None,
#     rates: int | None = None,
#     rates_list: typing.Sequence[int] | typing.Mapping[str, int] | None = None,
# ) -> typing.Mapping[str, spec.LoadTest]:
#     raise NotImplementedError()


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



