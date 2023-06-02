from __future__ import annotations

import typing

import flood


def generate_transaction_hashes(n: int, network: str) -> typing.Sequence[str]:
    return flood.load_samples(network=network, datatype='transactions', n=n)

