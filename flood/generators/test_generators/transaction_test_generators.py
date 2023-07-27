from __future__ import annotations

import typing

import flood
from flood.tests import load_tests


def generate_test_eth_get_transaction_by_hash(
    *,
    rates: typing.Sequence[int],
    duration: int | None = None,
    network: str,
    durations: typing.Sequence[int] | None = None,
    vegeta_args: flood.VegetaArgsShorthand | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.VegetaAttack]:
    n_calls = load_tests.estimate_call_count(
        rates=rates, duration=duration, durations=durations
    )
    calls = flood.generators.generate_calls_eth_get_transaction_by_hash(
        n_calls=n_calls,
        network=network,
        random_seed=random_seed,
    )
    return load_tests.create_load_test(
        calls=calls,
        rates=rates,
        duration=duration,
        durations=durations,
        vegeta_args=vegeta_args,
    )


def generate_test_eth_get_transaction_receipt(
    *,
    rates: typing.Sequence[int],
    duration: int | None = None,
    network: str,
    durations: typing.Sequence[int] | None = None,
    vegeta_args: flood.VegetaArgsShorthand | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.VegetaAttack]:
    n_calls = load_tests.estimate_call_count(
        rates=rates, duration=duration, durations=durations
    )
    calls = flood.generators.generate_calls_eth_get_transaction_receipt(
        n_calls=n_calls,
        network=network,
        random_seed=random_seed,
    )
    return load_tests.create_load_test(
        calls=calls,
        rates=rates,
        duration=duration,
        durations=durations,
        vegeta_args=vegeta_args,
    )
