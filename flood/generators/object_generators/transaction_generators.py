from __future__ import annotations

import typing

import flood


def generate_transaction_hashes(
    n: int,
    network: str,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[str]:
    return flood.load_samples(
        network=network,
        datatype='transactions',
        n=n,
        random_seed=random_seed,
    )
