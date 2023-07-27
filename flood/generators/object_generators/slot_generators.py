from __future__ import annotations

import typing
import flood
from flood import generators


def generate_slots(
    n: int,
    network: str,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[tuple[str, str]]:
    return generators.load_samples(
        network=network,
        datatype='slots',
        n=n,
        random_seed=random_seed,
    )
