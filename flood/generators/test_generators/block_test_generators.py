from __future__ import annotations

import typing

from flood import spec
import flood


def generate_test_eth_get_block_by_number(
    *,
    rates: typing.Sequence[int],
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    network: str,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    random_seed: spec.RandomSeed | None = None,
) -> flood.LoadTest:
    n_calls = flood.estimate_call_count(
        rates=rates, duration=duration, durations=durations
    )
    calls = flood.generate_calls_eth_get_block_by_number(
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


# def generate_test_eth_get_block_by_hash(
#     *,
#     rates: typing.Sequence[int],
#     duration: int | None = None,
#     durations: typing.Sequence[int] | None = None,
#     network: str,
#     vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
#     random_seed: spec.RandomSeed | None = None,
# ) -> flood.LoadTest:
#     n_calls = flood.estimate_call_count(
#         rates=rates, duration=duration, durations=durations
#     )
#     calls = flood.generate_calls_eth_get_block_by_hash(
#         n_calls=n_calls,
#         network=network,
#         random_seed=random_seed,
#     )
#     return flood.create_load_test(
#         calls=calls,
#         rates=rates,
#         duration=duration,
#         durations=durations,
#     )
