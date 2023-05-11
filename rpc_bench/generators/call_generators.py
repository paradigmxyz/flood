from __future__ import annotations

import ctc.rpc
import typing

from rpc_bench import spec


#
# # blocks
#


def create_calls_eth_get_block_by_number(
    block_numbers: typing.Sequence[int],
) -> typing.Sequence[spec.Call]:
    return [
        ctc.rpc.construct_eth_get_block_by_number(block_number=block_number)
        for block_number in block_numbers
    ]


def create_calls_eth_get_block_by_hash(
    block_hashes: typing.Sequence[str],
) -> typing.Sequence[spec.Call]:
    return [
        ctc.rpc.construct_eth_get_block_by_hash(block_hash=block_hash)
        for block_hash in block_hashes
    ]


#
# # addresses
#


def create_calls_eth_get_eth_balance(
    addresses: typing.Sequence[str],
    block_numbers: typing.Sequence[int],
) -> typing.Sequence[spec.Call]:
    return [
        ctc.rpc.construct_eth_get_balance(
            address=address, block_number=block_number
        )
        for address, block_number in zip(addresses, block_numbers)
    ]


def create_calls_eth_get_eth_transaction_count(
    addresses: typing.Sequence[str],
    block_numbers: typing.Sequence[int],
) -> typing.Sequence[spec.Call]:
    return [
        ctc.rpc.construct_eth_get_transaction_count(
            from_address=address, block_number=block_number
        )
        for address, block_number in zip(addresses, block_numbers)
    ]


#
# # transactions
#


def create_calls_eth_get_transaction_by_hash(
    transaction_hashes: typing.Sequence[str],
) -> typing.Sequence[spec.Call]:
    return [
        ctc.rpc.construct_eth_get_transaction_by_hash(
            transaction_hash=transaction_hash
        )
        for transaction_hash in transaction_hashes
    ]


def create_calls_eth_get_transaction_receipt(
    transaction_hashes: typing.Sequence[str],
) -> typing.Sequence[spec.Call]:
    return [
        ctc.rpc.construct_eth_get_transaction_receipt(
            transaction_hash=transaction_hash
        )
        for transaction_hash in transaction_hashes
    ]


#
# # logs
#


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


#
# # contracts
#


def create_calls_eth_get_code(
    addresses: typing.Sequence[str],
    block_numbers: typing.Sequence[int | typing.Literal['latest']] | None,
) -> typing.Sequence[spec.Call]:
    if block_numbers is None:
        block_numbers = ['latest'] * len(addresses)
    return [
        ctc.rpc.construct_eth_get_code(
            address=address, block_number=block_number
        )
        for address, block_number in zip(addresses, block_numbers)
    ]


def create_calls_eth_get_storage_at(
    slots: typing.Sequence[tuple[str, str]],
    block_numbers: typing.Sequence[int | typing.Literal['latest']] | None,
) -> typing.Sequence[spec.Call]:
    if block_numbers is None:
        block_numbers = ['latest'] * len(slots)
    return [
        ctc.rpc.construct_eth_get_storage_at(
            address=address, position=slot, block_number=block_number
        )
        for (address, slot), block_number in zip(slots, block_numbers)
    ]

# def create_calls_eth_call(
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

