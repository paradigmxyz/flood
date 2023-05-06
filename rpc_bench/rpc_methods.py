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
    methods: typing.Sequence[str],
    samples: int,
    *,
    random_seed: int | None = None,
) -> spec.MethodCalls:

    if random_seed is None:
        random_seed = 0

    calls: spec.MethodCalls = {method: [] for method in methods}
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

