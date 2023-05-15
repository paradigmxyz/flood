from __future__ import annotations

import typing

import rpc_bench
from rpc_bench import spec


def generate_test_eth_get_balance(
    rates: typing.Sequence[int],
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    random_seed: spec.RandomSeed | None = None,
) -> spec.LoadTest:
    n_calls = rpc_bench.estimate_call_count(
        rates=rates, duration=duration, durations=durations
    )
    calls = rpc_bench.generate_calls_eth_get_eth_balance(n_calls=n_calls)
    return rpc_bench.construct_load_test(
        calls=calls,
        rates=rates,
        duration=duration,
        durations=durations,
    )


def generate_test_eth_get_transaction_count(
    rates: typing.Sequence[int],
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    random_seed: spec.RandomSeed | None = None,
) -> spec.LoadTest:
    n_calls = rpc_bench.estimate_call_count(
        rates=rates, duration=duration, durations=durations
    )
    calls = rpc_bench.generate_calls_eth_get_transaction_count(n_calls=n_calls)
    return rpc_bench.construct_load_test(
        calls=calls,
        rates=rates,
        duration=duration,
        durations=durations,
    )

