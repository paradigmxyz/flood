from __future__ import annotations

import typing

import rpc_bench


def get_all_equality_tests() -> typing.Sequence[rpc_bench.EqualityTest]:
    return list(get_vanilla_equality_tests()) + list(get_trace_equality_tests())


def get_vanilla_equality_tests() -> typing.Sequence[rpc_bench.EqualityTest]:
    import ctc.rpc

    return [
        (
            'eth_getChainId',
            ctc.rpc.construct_eth_chain_id,
            [],
            {},
        ),
        (
            'eth_getLogs',
            ctc.rpc.construct_eth_get_logs,
            [],
            {
                'address': '0x6b175474e89094c44da98b954eedeac495271d0f',
                'start_block': 14_000_000,
                'end_block': 14_000_100,
            },
        ),
        (
            'eth_gasPrice',
            ctc.rpc.construct_eth_chain_id,
            [],
            {},
        ),
        (
            'eth_getBalance',
            ctc.rpc.construct_eth_get_balance,
            ['0xeb27d00030033c29307daa483171d22eb0c93342'],
            # ['0xe540c45c504b348ad4d6eb9344e6cfa07c959be6'],
            {
                'block_number': 16_000_000,
            },
        ),
        (
            'eth_getTransactionCount',
            ctc.rpc.construct_eth_get_transaction_count,
            ['0xeb27d00030033c29307daa483171d22eb0c93342'],
            {
                'block_number': 16_000_000,
            },
        ),
        (
            'eth_getStorageAt',
            ctc.rpc.construct_eth_get_storage_at,
            [],
            {
                'address': '0x4d9079bb4165aeb4084c526a32695dcfd2f77381',
                'position': '0x0000000000000000000000000000000000000000000000000000000000000002',
                'block_number': 16_100_000,
            },
        ),
        (
            'eth_getCode',
            ctc.rpc.construct_eth_get_code,
            ['0x4d9079bb4165aeb4084c526a32695dcfd2f77381'],
            {},
        ),
        (
            'eth_getBlockByNumber',
            ctc.rpc.construct_eth_get_block_by_number,
            [16_000_000],
            {},
        ),
        (
            'eth_getBlockByHash',
            ctc.rpc.construct_eth_get_block_by_hash,
            [
                '0x3dc4ef568ae2635db1419c5fec55c4a9322c05302ae527cd40bff380c1d465dd'
            ],
            {},
        ),
        (
            'eth_getTransactionByHash',
            ctc.rpc.construct_eth_get_transaction_by_hash,
            [
                '0xd01212e8ab48d2fd2ea9c4f33f8670fd1cf0cfb09d2e3c6ceddfaf54152386e5'
            ],
            {},
        ),
        (
            'eth_getTransactionReceipt',
            ctc.rpc.construct_eth_get_transaction_receipt,
            [
                '0xd01212e8ab48d2fd2ea9c4f33f8670fd1cf0cfb09d2e3c6ceddfaf54152386e5'
            ],
            {},
        ),
        (
            'eth_call',
            ctc.rpc.construct_eth_call,
            [],
            {
                'to_address': '0x6b175474e89094c44da98b954eedeac495271d0f',
                'function_abi': {
                    'constant': True,
                    'inputs': [
                        {
                            'internalType': 'address',
                            'name': '',
                            'type': 'address',
                        }
                    ],
                    'name': 'balanceOf',
                    'outputs': [
                        {
                            'internalType': 'uint256',
                            'name': '',
                            'type': 'uint256',
                        }
                    ],
                    'payable': False,
                    'stateMutability': 'view',
                    'type': 'function',
                },
                'function_parameters': [
                    '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643'
                ],
                'block_number': 16_000_000,
            },
        ),
    ]


def get_trace_equality_tests() -> typing.Sequence[rpc_bench.EqualityTest]:
    import ctc.rpc

    function_abi = {
        'constant': True,
        'inputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
        'name': 'balanceOf',
        'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}],
        'payable': False,
        'stateMutability': 'view',
        'type': 'function',
    }

    return [
        (
            'trace_block',
            ctc.rpc.construct_trace_block,
            [],
            {'block_number': 16_000_000},
        ),
        (
            'trace_call',
            ctc.rpc.construct_trace_call,
            [],
            {
                'to_address': '0x6b175474e89094c44da98b954eedeac495271d0f',
                'trace_type': ['trace'],
                'function_abi': function_abi,
                'function_parameters': [
                    '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643'
                ],
                'block_number': 16_000_000,
            },
        ),
        (
            'trace_call_many',
            ctc.rpc.construct_trace_call_many,
            [],
            {
                'calls': [
                    {
                        'to_address': '0x6b175474e89094c44da98b954eedeac495271d0f',
                        'function_abi': function_abi,
                        'function_parameters': [
                            '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643'
                        ],
                        'trace_type': ['trace'],
                    },
                ],
                'trace_type': ['trace'],
            },
        ),
        #     (
        #         'trace_filter',
        #         ctc.rpc.construct_trace_filter,
        #         [],
        #         {
        #             'to_addresses': ['0x6b175474e89094c44da98b954eedeac495271d0f'],
        #             'start_block': 10_000_000,
        #             'end_block': 10_000_001,
        #             'count': 10,
        #         }
        #     ),
        #     (
        #         'trace_get',
        #         ctc.rpc.construct_trace_get,
        #         [],
        #         {}
        #     ),
        #     (
        #         'trace_raw_transaction',
        #         ctc.rpc.construct_trace_raw_transaction,
        #         ['0xd01212e8ab48d2fd2ea9c4f33f8670fd1cf0cfb09d2e3c6ceddfaf54152386e5'],
        #         {'trace_type': ['trace']},
        #     ),
        (
            'trace_replay_block_transactions',
            ctc.rpc.construct_trace_replay_block_transactions,
            [],
            {
                'block_number': 16_000_000,
                'trace_type': ['trace'],
            },
        ),
        (
            'trace_replay_transaction',
            ctc.rpc.construct_trace_replay_transaction,
            [
                '0xd01212e8ab48d2fd2ea9c4f33f8670fd1cf0cfb09d2e3c6ceddfaf54152386e5'
            ],
            {'trace_type': ['trace']},
        ),
        (
            'trace_transaction',
            ctc.rpc.construct_trace_transaction,
            [
                '0xd01212e8ab48d2fd2ea9c4f33f8670fd1cf0cfb09d2e3c6ceddfaf54152386e5'
            ],
            {},
        ),
    ]

