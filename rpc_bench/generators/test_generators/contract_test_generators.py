from __future__ import annotations

import typing

import rpc_bench


def generate_test_eth_get_code(
    rates: typing.Sequence[int],
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    random_seed: rpc_bench.RandomSeed | None = None,
) -> rpc_bench.LoadTest:
    n_calls = rpc_bench.estimate_call_count(
        rates=rates, duration=duration, durations=durations
    )
    calls = rpc_bench.generate_calls_eth_get_code(n_calls=n_calls)
    return rpc_bench.construct_load_test(
        calls=calls,
        rates=rates,
        duration=duration,
        durations=durations,
    )


def generate_test_eth_get_storage_at(
    rates: typing.Sequence[int],
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    random_seed: rpc_bench.RandomSeed | None = None,
) -> rpc_bench.LoadTest:
    n_calls = rpc_bench.estimate_call_count(
        rates=rates, duration=duration, durations=durations
    )
    calls = rpc_bench.generate_calls_eth_get_storage_at(n_calls=n_calls)
    return rpc_bench.construct_load_test(
        calls=calls,
        rates=rates,
        duration=duration,
        durations=durations,
    )

