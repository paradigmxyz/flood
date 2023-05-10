from __future__ import annotations

import ctc.rpc
import typing

from rpc_bench import spec

if typing.TYPE_CHECKING:
    import numpy as np


def create_calls_eth_get_logs(
    contract_address: str,
    topics: typing.Sequence[str | None],
    block_ranges: typing.Sequence[tuple[int, int]],
) -> typing.Sequence[spec.Call]:
    return [
        ctc.rpc.construct_eth_get_logs(
            address=contract_address,
            topics=topics,
            start_block=start_block,
            end_block=end_block,
        )
        for start_block, end_block in block_ranges
    ]


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
    random_seed: int | np.random._generator.Generator | None = None,
) -> typing.Sequence[int]:
    import numpy as np

    # seed a generator
    if random_seed is None:
        random_seed = 0
    if isinstance(random_seed, int):
        gen = np.random.Generator(np.random.PCG64(random_seed))

    # generate blocks
    all_blocks = np.arange(start_block, end_block + 1)
    chosen = gen.choice(all_blocks, size=n, replace=replace)

    # sort
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
    random_seed: int | np.random._generator.Generator | None = None,
) -> typing.Sequence[tuple[int, int]]:
    import numpy as np

    # seed a generator
    if random_seed is None:
        random_seed = 0
    if isinstance(random_seed, int):
        gen = np.random.Generator(np.random.PCG64(random_seed))

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
        # record attempt
        attempt += 1
        if attempt > n_attempts:
            raise Exception(
                'could not find block range set after '
                + str(n_attempts)
                + ' attempts'
            )

        # create new candidate
        try:
            start = next(candidates)
        except StopIteration:
            start = gen.integers(start_block, end_block)
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
        gen.shuffle(ranges_list)
        return ranges_list

