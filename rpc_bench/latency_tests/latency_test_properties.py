from __future__ import annotations

import typing


def estimate_call_count(
    rates: typing.Sequence[int],
    duration: int = 5,
    *,
    n_repeats: int | None = None,
) -> int:
    n_calls = sum(duration * rate for rate in rates)
    if n_repeats is not None:
        n_calls *= n_repeats
    return n_calls

