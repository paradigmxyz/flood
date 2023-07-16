from __future__ import annotations

import typing

from flood import spec

if typing.TYPE_CHECKING:
    import numpy as np


def get_rng(random_seed: spec.RandomSeed | None = None) -> np.random.Generator:
    import numpy as np

    if random_seed is None:
        import time

        random_seed = int(time.time())
    if isinstance(random_seed, int):
        gen = np.random.Generator(np.random.PCG64(random_seed))
    if isinstance(gen, np.random.Generator):
        return gen
    else:
        raise Exception('invalid seed format: ' + str(type(random_seed)))
