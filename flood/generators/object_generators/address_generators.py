from __future__ import annotations

import typing

import flood


def generate_contract_addresses(
    n: int,
    network: str,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[str]:
    return flood.load_samples(
        network=network,
        datatype='contracts',
        n=n,
        random_seed=random_seed,
    )


def generate_eoas(
    n: int,
    network: str,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[str]:
    return flood.load_samples(
        network=network,
        datatype='eoas',
        n=n,
        random_seed=random_seed,
    )
