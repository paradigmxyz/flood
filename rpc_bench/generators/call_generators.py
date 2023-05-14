from __future__ import annotations

import ctc.rpc
import typing

from rpc_bench import spec
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
    block_numbers: typing.Sequence[int] | None = None,
) -> typing.Sequence[spec.Call]:
    if block_numbers is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            n=n_calls,
            random_seed=0,
            start_block=0,
            end_block=16_000_000,
        )
    return [
        ctc.rpc.construct_eth_get_block_by_number(block_number=block_number)
        for block_number in block_numbers
    ]


def generate_calls_eth_get_block_by_hash(
    n_calls: int | None = None,
    *,
    block_hashes: typing.Sequence[str] | None = None,
) -> typing.Sequence[spec.Call]:
    if block_hashes is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        block_hashes = block_generators.generate_block_hashes(
            n=n_calls,
        )
    return [
        ctc.rpc.construct_eth_get_block_by_hash(block_hash=block_hash)
        for block_hash in block_hashes
    ]


#
# # addresses
#


def generate_calls_eth_get_eth_balance(
    n_calls: int | None = None,
    *,
    addresses: typing.Sequence[str] | None = None,
    block_numbers: typing.Sequence[int] | None = None,
) -> typing.Sequence[spec.Call]:
    if block_numbers is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            start_block=10_000_000,
            end_block=16_000_000,
            n=n_calls,
            random_seed=0,
        )
    if addresses is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        addresses = address_generators.generate_contract_addresses(n_calls)

    return [
        ctc.rpc.construct_eth_get_balance(
            address=address, block_number=block_number
        )
        for address, block_number in zip(addresses, block_numbers)
    ]


def generate_calls_eth_get_transaction_count(
    n_calls: int | None = None,
    *,
    addresses: typing.Sequence[str] | None = None,
    block_numbers: typing.Sequence[int] | None = None,
) -> typing.Sequence[spec.Call]:
    if block_numbers is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            start_block=10_000_000,
            end_block=16_000_000,
            n=n_calls,
            random_seed=0,
        )
    if addresses is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        addresses = address_generators.generate_eoas(n_calls)

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
    transaction_hashes: typing.Sequence[str] | None = None,
) -> typing.Sequence[spec.Call]:
    if transaction_hashes is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        transaction_hashes = transaction_generators.generate_transaction_hashes(
            n_calls
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
    transaction_hashes: typing.Sequence[str] | None = None,
) -> typing.Sequence[spec.Call]:
    if transaction_hashes is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        transaction_hashes = transaction_generators.generate_transaction_hashes(
            n_calls
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

contracts = {
    'USDC': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
    'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f',
    'LUSD': '0x5f98805a4e8be255a32880fdec7f6728c6568ba0',
}

event_hashes = {
    'Transfer': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
    'Approval': '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925',
}


def generate_calls_eth_get_logs(
    n_calls: int | None = None,
    *,
    contract_address: str | None = None,
    topics: typing.Sequence[str | None] | None = None,
    block_ranges: typing.Sequence[tuple[int, int]] | None = None,
) -> typing.Sequence[spec.Call]:
    if contract_address is None:
        contract_address = contracts['USDC']
    if block_ranges is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        block_ranges = block_generators.generate_block_ranges(
            start_block=10_000_000,
            end_block=16_000_000,
            n=n_calls,
            range_size=100,
            random_seed=0,
        )
    if topics is None:
        topics = [event_hashes['Transfer']]
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
    addresses: typing.Sequence[str] | None = None,
    block_numbers: typing.Sequence[int | typing.Literal['latest']]
    | None = None,
) -> typing.Sequence[spec.Call]:
    if block_numbers is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            start_block=10_000_000,
            end_block=16_000_000,
            n=n_calls,
            random_seed=0,
        )
    if addresses is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        addresses = address_generators.generate_contract_addresses(n_calls)
    return [
        ctc.rpc.construct_eth_get_code(
            address=address, block_number=block_number
        )
        for address, block_number in zip(addresses, block_numbers)
    ]


def generate_calls_eth_get_storage_at(
    n_calls: int | None = None,
    *,
    slots: typing.Sequence[tuple[str, str]] | None = None,
    block_numbers: typing.Sequence[int | typing.Literal['latest']]
    | None = None,
) -> typing.Sequence[spec.Call]:
    if block_numbers is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        block_numbers = block_generators.generate_block_numbers(
            start_block=10_000_000,
            end_block=16_000_000,
            n=n_calls,
            random_seed=0,
        )
    if slots is None:
        if n_calls is None:
            raise Exception('must specify more parameters')
        slots = slot_generators.generate_slots(n_calls)
    return [
        ctc.rpc.construct_eth_get_storage_at(
            address=address, position=slot, block_number=block_number
        )
        for (address, slot), block_number in zip(slots, block_numbers)
    ]


# def generate_calls_eth_call(
#     addresses: typing.Sequence[str],
#     block_numbers: typing.Sequence[int] | None,
# ) -> typing.Sequence[spec.Call]:
#     if block_numbers is None:
#         block_numbers = [None] * len(addresses)
#     return [
#         ctc.rpc.construct_eth_get_storage_at(
#             address=address, block_number=block_number
#         )
#         for address, block_number in zip(addresses, block_numbers)
#     ]

