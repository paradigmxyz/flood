from __future__ import annotations

import ctc.rpc
import typing

from rpc_bench import spec


def get_all_methods() -> typing.Sequence[str]:
    return [
        'eth_blockNumber',
        'eth_chainId',
        'eth_hashRate',
    ]


def create_calls(
    methods: typing.Sequence[str] | None = None,
    samples: int | None = None,
    *,
    random_seed: int | None = None,
    calls_file: str | None = None,
) -> spec.MethodCalls:
    calls: spec.MethodCalls

    # load calls from file
    if calls_file is not None:
        import json

        with open(calls_file, 'r') as f:
            calls_data = json.load(f)
            return {
                method: calls_data['calls'][method]
                for method in calls_data['methods']
            }

    # parse inputs
    if samples is None:
        samples = 1
    if methods is None:
        methods = get_all_methods()
    if random_seed is None:
        random_seed = 0

    # generate calls
    calls = {method: [] for method in methods}
    for method in methods:
        call_creator = _get_call_creator(method)
        for sample in range(samples):
            call = call_creator()
            calls[method].append(call)  # type: ignore

    return calls


def _get_call_creator(method: str) -> typing.Callable[..., typing.Any]:
    if method == 'eth_blockNumber':
        return ctc.rpc.construct_eth_block_number
    elif method == 'eth_chainId':
        return ctc.rpc.construct_eth_chain_id
    elif method == 'eth_hashRate':
        return ctc.rpc.construct_eth_hashrate
    else:
        raise ValueError('unknown method: ' + str(method))


def choose_random_blocks(
    n: int,
    start_block: int,
    end_block: int,
    *,
    replace: bool = False,
    sort: bool = False,
) -> typing.Sequence[int]:
    import numpy as np

    all_blocks = np.arange(start_block, end_block + 1)
    chosen = np.random.choice(all_blocks, size=n, replace=replace)
    if sort:
        return sorted(chosen)
    else:
        return list(chosen)


def choose_random_block_ranges(
    *,
    n: int,
    range_size: int,
    start_block: int,
    end_block: int,
    non_overlapping: bool = True,
    sort: bool = False,
    n_attempts: int = 1_000_000,
) -> typing.Sequence[tuple[int, int]]:
    import random

    # create starting sample
    start_blocks = choose_random_blocks(
        n=n,
        start_block=start_block,
        end_block=end_block,
        replace=non_overlapping,
    )
    candidates = iter(start_blocks)

    # create ranges
    attempt = 0
    ranges: set[tuple[int, int]] = set()
    while len(ranges) < n:
        attempt += 1
        if attempt > n_attempts:
            raise Exception(
                'could not find block range set after '
                + str(n_attempts)
                + ' attempts'
            )

        # ceate new candidate
        try:
            start = next(candidates)
        except StopIteration:
            start = random.randint(start_block, end_block)
        end = start + range_size
        candidate = (start, end)

        # check whether candidate is valid
        if candidate in ranges:
            continue
        if end > end_block:
            continue
        if non_overlapping:
            skip = False
            for other_start, other_end in ranges:
                if other_start <= end and other_end >= start:
                    skip = True
                    break
            if skip:
                continue

        ranges.add(candidate)

    # sort
    if sort:
        return sorted(ranges)
    else:
        ranges_list = list(ranges)
        random.shuffle(ranges_list)
        return ranges_list

