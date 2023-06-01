from __future__ import annotations

import ctc.rpc
import typing

from flood import spec


def _get_all_methods() -> typing.Sequence[str]:
    return [
        'eth_blockNumber',
        'eth_chainId',
        'eth_hashRate',
    ]


def _create_calls(
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
        methods = _get_all_methods()
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

