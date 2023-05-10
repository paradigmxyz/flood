from __future__ import annotations

import typing


def estimate_call_count(
    rates: typing.Sequence[int],
    duration: int = 5,
    *,
    n_repeats: int | None = None,
) -> int:
    n_calls = sum(duration * rate for rate in rates)
    if n_repeats is not None:
        n_calls *= n_repeats
    return n_calls


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

