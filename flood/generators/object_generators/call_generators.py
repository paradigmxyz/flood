from __future__ import annotations

import typing

import flood
from flood import generators
from . import address_generators
from . import block_generators
from . import slot_generators
from . import transaction_generators


#
# # blocks
#


def generate_calls_eth_get_block_by_number(
    n_calls: int | None = None,
    *,
    network: str | None = None,
    block_numbers: typing.Sequence[int] | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if block_numbers is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            n=n_calls,
            random_seed=random_seed,
            start_block=0,
            end_block=16_000_000,
            network=network,
        )
    return [
        ctc.rpc.construct_eth_get_block_by_number(block_number=block_number)
        for block_number in block_numbers
    ]


def generate_calls_eth_get_block_by_hash(
    n_calls: int | None = None,
    *,
    network: str | None = None,
    block_hashes: typing.Sequence[str] | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if block_hashes is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        block_hashes = block_generators.generate_block_hashes(
            n=n_calls,
            network=network,
            random_seed=random_seed,
        )
    return [
        ctc.rpc.construct_eth_get_block_by_hash(block_hash=block_hash)
        for block_hash in block_hashes
    ]


def generate_calls_eth_fee_history(
    n_calls: int | None = None,
    *,
    network: str | None = None,
    random_seed: flood.RandomSeed | None = None,
    block_numbers: typing.Sequence[int] | None = None,
    block_count: int | None = None
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if block_numbers is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            n=n_calls,
            random_seed=random_seed,
            start_block=13_000_000,
            end_block=17_000_000,
            network=network,
        )
    if block_count is None:
        block_count = 1024

    return [
        ctc.rpc.construct_eth_fee_history(
            block_number,
            block_count=block_count,
        )
        for block_number in block_numbers
    ]


#
# # addresses
#


def generate_calls_eth_get_eth_balance(
    n_calls: int | None = None,
    *,
    network: str,
    addresses: typing.Sequence[str] | None = None,
    block_numbers: typing.Sequence[int] | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if block_numbers is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            start_block=10_000_000,
            end_block=16_000_000,
            n=n_calls,
            random_seed=random_seed,
            network=network,
        )
    if addresses is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        addresses = address_generators.generate_contract_addresses(
            n_calls,
            network=network,
            random_seed=random_seed,
        )

    return [
        ctc.rpc.construct_eth_get_balance(
            address=address, block_number=block_number
        )
        for address, block_number in zip(addresses, block_numbers)
    ]


def generate_calls_eth_get_transaction_count(
    n_calls: int | None = None,
    *,
    network: str,
    addresses: typing.Sequence[str] | None = None,
    block_numbers: typing.Sequence[int] | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if block_numbers is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            start_block=10_000_000,
            end_block=16_000_000,
            n=n_calls,
            random_seed=random_seed,
            network=network,
        )
    if addresses is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        addresses = address_generators.generate_eoas(
            n_calls,
            network=network,
            random_seed=random_seed,
        )

    return [
        ctc.rpc.construct_eth_get_transaction_count(
            from_address=address, block_number=block_number
        )
        for address, block_number in zip(addresses, block_numbers)
    ]


#
# # transactions
#


def generate_calls_eth_get_transaction_by_hash(
    n_calls: int | None = None,
    *,
    network: str,
    transaction_hashes: typing.Sequence[str] | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if transaction_hashes is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        transaction_hashes = transaction_generators.generate_transaction_hashes(
            n_calls,
            network=network,
            random_seed=random_seed,
        )
    return [
        ctc.rpc.construct_eth_get_transaction_by_hash(
            transaction_hash=transaction_hash
        )
        for transaction_hash in transaction_hashes
    ]


def generate_calls_eth_get_transaction_receipt(
    n_calls: int | None = None,
    *,
    network: str,
    transaction_hashes: typing.Sequence[str] | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if transaction_hashes is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        transaction_hashes = transaction_generators.generate_transaction_hashes(
            n_calls,
            network=network,
            random_seed=random_seed,
        )
    return [
        ctc.rpc.construct_eth_get_transaction_receipt(
            transaction_hash=transaction_hash
        )
        for transaction_hash in transaction_hashes
    ]


#
# # logs
#

_default_contracts = {
    'USDC': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
    'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f',
    'LUSD': '0x5f98805a4e8be255a32880fdec7f6728c6568ba0',
}

_default_event_hashes = {
    'Transfer': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',  # noqa: E501
    'Approval': '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925',  # noqa: E501
}


def generate_calls_eth_get_logs(
    n_calls: int | None = None,
    *,
    contract_address: str | None = None,
    topics: typing.Sequence[str | None] | None = None,
    block_ranges: typing.Sequence[tuple[int, int]] | None = None,
    block_range_size: int | None = None,
    network: str | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if contract_address is None:
        contract_address = _default_contracts['USDC']
    if block_ranges is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        if block_range_size is None:
            block_range_size = 100
        block_ranges = block_generators.generate_block_ranges(
            start_block=10_000_000,
            end_block=16_000_000,
            n=n_calls,
            range_size=block_range_size,
            random_seed=random_seed,
            network=network,
        )
    if topics is None:
        topics = [_default_event_hashes['Transfer']]
    return [
        ctc.rpc.construct_eth_get_logs(
            address=contract_address,
            topics=topics,
            start_block=start_block,
            end_block=end_block,
        )
        for start_block, end_block in block_ranges
    ]


#
# # contracts
#


def generate_calls_eth_get_code(
    n_calls: int | None = None,
    *,
    network: str,
    addresses: typing.Sequence[str] | None = None,
    block_numbers: typing.Sequence[int | typing.Literal['latest']]
    | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if block_numbers is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            start_block=10_000_000,
            end_block=16_000_000,
            n=n_calls,
            random_seed=random_seed,
            network=network,
        )
    if addresses is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        addresses = address_generators.generate_contract_addresses(
            n_calls,
            network=network,
            random_seed=random_seed,
        )
    return [
        ctc.rpc.construct_eth_get_code(
            address=address, block_number=block_number
        )
        for address, block_number in zip(addresses, block_numbers)
    ]


def generate_calls_eth_get_storage_at(
    n_calls: int | None = None,
    *,
    network: str,
    slots: typing.Sequence[tuple[str, str]] | None = None,
    block_numbers: typing.Sequence[int | typing.Literal['latest']]
    | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if block_numbers is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            start_block=10_000_000,
            end_block=16_000_000,
            n=n_calls,
            random_seed=random_seed,
            network=network,
        )
    if slots is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        slots = slot_generators.generate_slots(
            n_calls, network=network, random_seed=random_seed
        )
    return [
        ctc.rpc.construct_eth_get_storage_at(
            address=address, position=slot, block_number=block_number
        )
        for (address, slot), block_number in zip(slots, block_numbers)
    ]


_default_call_datas = {
    'decimals': '0x313ce567',
    'totalSupply': '0x18160ddd',
    'symbol': '0x95d89b41',
}


def generate_calls_eth_call(
    n_calls: int,
    network: str,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if network != 'ethereum':
        raise Exception('only ethereum supported for eth_call')

    rng = generators.get_rng(random_seed=random_seed)
    contract_addresses = rng.choice(
        list(_default_contracts.values()),
        size=n_calls,
    )
    call_datas = rng.choice(
        list(_default_call_datas.values()),
        size=n_calls,
    )
    block_numbers = block_generators.generate_block_numbers(
        start_block=10_000_000,
        end_block=16_000_000,
        n=n_calls,
        random_seed=random_seed,
        network=network,
    )

    return [
        ctc.rpc.construct_eth_call(
            to_address=contract_address,
            call_data=call_data,
            block_number=block_number,
        )
        for contract_address, call_data, block_number in zip(
            contract_addresses, call_datas, block_numbers
        )
    ]


#
# # traces
#


def generate_calls_trace_block(
    n_calls: int | None = None,
    *,
    block_numbers: typing.Sequence[int] | None = None,
    network: str | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if block_numbers is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            n=n_calls,
            random_seed=0,
            start_block=0,
            end_block=16_000_000,
            network=network,
        )
    return [
        ctc.rpc.construct_trace_block(block_number=block_number)
        for block_number in block_numbers
    ]


def generate_calls_trace_transaction(
    n_calls: int | None = None,
    *,
    transaction_hashes: typing.Sequence[str] | None = None,
    network: str | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if transaction_hashes is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        if network is None:
            raise Exception('must floodify network')
        transaction_hashes = transaction_generators.generate_transaction_hashes(
            n=n_calls,
            network=network,
            random_seed=random_seed,
        )
    return [
        ctc.rpc.construct_trace_transaction(transaction_hash=transaction_hash)
        for transaction_hash in transaction_hashes
    ]


def generate_calls_trace_replay_block_transactions(
    n_calls: int | None = None,
    *,
    block_numbers: typing.Sequence[int] | None = None,
    network: str | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if block_numbers is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            n=n_calls,
            random_seed=random_seed,
            start_block=0,
            end_block=16_000_000,
            network=network,
        )
    return [
        ctc.rpc.construct_trace_replay_block_transactions(
            block_number=block_number,
            trace_type=['trace'],
        )
        for block_number in block_numbers
    ]


def generate_calls_trace_replay_block_transactions_state_diff(
    n_calls: int | None = None,
    *,
    block_numbers: typing.Sequence[int] | None = None,
    network: str | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if block_numbers is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            n=n_calls,
            random_seed=random_seed,
            start_block=0,
            end_block=16_000_000,
            network=network,
        )
    return [
        ctc.rpc.construct_trace_replay_block_transactions(
            block_number=block_number,
            trace_type=['stateDiff'],
        )
        for block_number in block_numbers
    ]


def generate_calls_trace_replay_block_transactions_vm_trace(
    n_calls: int | None = None,
    *,
    block_numbers: typing.Sequence[int] | None = None,
    network: str | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if block_numbers is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            n=n_calls,
            random_seed=random_seed,
            start_block=0,
            end_block=16_000_000,
            network=network,
        )
    return [
        ctc.rpc.construct_trace_replay_block_transactions(
            block_number=block_number,
            trace_type=['vmTrace'],
        )
        for block_number in block_numbers
    ]


def generate_calls_trace_replay_transaction(
    n_calls: int | None = None,
    *,
    transaction_hashes: typing.Sequence[str] | None = None,
    network: str | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if transaction_hashes is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        if network is None:
            raise Exception('must floodify network')
        transaction_hashes = transaction_generators.generate_transaction_hashes(
            n=n_calls,
            random_seed=random_seed,
            network=network,
        )
    return [
        ctc.rpc.construct_trace_replay_transaction(
            transaction_hash=transaction_hash,
            trace_type=['trace'],
        )
        for transaction_hash in transaction_hashes
    ]


def generate_calls_trace_replay_transaction_state_diff(
    n_calls: int | None = None,
    *,
    transaction_hashes: typing.Sequence[str] | None = None,
    network: str | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if transaction_hashes is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        if network is None:
            raise Exception('must floodify network')
        transaction_hashes = transaction_generators.generate_transaction_hashes(
            n=n_calls,
            random_seed=random_seed,
            network=network,
        )
    return [
        ctc.rpc.construct_trace_replay_transaction(
            transaction_hash=transaction_hash,
            trace_type=['stateDiff'],
        )
        for transaction_hash in transaction_hashes
    ]


def generate_calls_trace_replay_transaction_vm_trace(
    n_calls: int | None = None,
    *,
    transaction_hashes: typing.Sequence[str] | None = None,
    network: str | None = None,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[flood.Call]:
    import ctc.rpc

    if transaction_hashes is None:
        if n_calls is None:
            raise Exception('must floodify more parameters')
        if network is None:
            raise Exception('must floodify network')
        transaction_hashes = transaction_generators.generate_transaction_hashes(
            n=n_calls,
            random_seed=random_seed,
            network=network,
        )
    return [
        ctc.rpc.construct_trace_replay_transaction(
            transaction_hash=transaction_hash,
            trace_type=['vmTrace'],
        )
        for transaction_hash in transaction_hashes
    ]
