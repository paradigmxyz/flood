from __future__ import annotations

import typing

import flood


def generate_test_eth_get_code(
    *,
    rates: typing.Sequence[int],
    network: str,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> flood.LoadTest:
    n_calls = flood.estimate_call_count(
        rates=rates, duration=duration, durations=durations
    )
    calls = flood.generate_calls_eth_get_code(
        n_calls=n_calls,
        network=network,
        random_seed=random_seed,
    )
    return flood.create_load_test(
        calls=calls,
        rates=rates,
        duration=duration,
        durations=durations,
    )


def generate_test_eth_get_storage_at(
    *,
    rates: typing.Sequence[int],
    network: str,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> flood.LoadTest:
    n_calls = flood.estimate_call_count(
        rates=rates, duration=duration, durations=durations
    )
    calls = flood.generate_calls_eth_get_storage_at(
        n_calls=n_calls,
        network=network,
        random_seed=random_seed,
    )
    return flood.create_load_test(
        calls=calls,
        rates=rates,
        duration=duration,
        durations=durations,
    )


def generate_test_eth_call(
    *,
    rates: typing.Sequence[int],
    network: str,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> flood.LoadTest:
    n_calls = flood.estimate_call_count(
        rates=rates, duration=duration, durations=durations
    )
    calls = flood.generate_calls_eth_call(
        n_calls=n_calls,
        network=network,
        random_seed=random_seed,
    )
    return flood.create_load_test(
        calls=calls,
        rates=rates,
        duration=duration,
        durations=durations,
    )
