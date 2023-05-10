from __future__ import annotations

import typing

import rpc_bench


contracts = {
    'USDC': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
    'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f',
    'LUSD': '0x5f98805a4e8be255a32880fdec7f6728c6568ba0',
}

event_hashes = {
    'Transfer': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
    'Approval': '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925',
}


def create_load_tests_eth_get_logs_by_url(
    urls: typing.Sequence[str] | typing.Mapping[str, str],
    rates: typing.Sequence[int],
    duration: int,
) -> typing.Mapping[str, rpc_bench.LoadTest]:

    if isinstance(urls, list):
        urls = {url: url for url in urls}
    if not isinstance(urls, dict):
        raise Exception('could not convert urls')

    n_calls = rpc_bench.estimate_call_count(rates=rates, duration=duration)

    block_ranges = rpc_bench.choose_random_block_ranges(
        start_block=10_000_000,
        end_block=16_000_000,
        n=n_calls,
        range_size=100,
        random_seed=0,
    )

    calls = rpc_bench.create_calls_eth_get_logs(
        contract_address=contracts['USDC'],
        topics=[event_hashes['Transfer']],
        block_ranges=block_ranges,
    )

    tests: typing.MutableMapping[str, rpc_bench.LoadTest] = {}
    for name, url in urls.items():
        tests[name] = {
            'url': url,
            'rates': rates,
            'duration': duration,
            'calls': calls,
        }

    return tests


def create_load_tests_eth_get_logs_by_contract(
    url: str,
    rates: typing.Sequence[int],
    duration: int,
    range_size: int,
) -> typing.Mapping[str, rpc_bench.LoadTest]:
    """test: Transfers of USDC vs DAI vs LUSD"""

    n_calls = rpc_bench.estimate_call_count(rates=rates, duration=duration)

    block_ranges = rpc_bench.choose_random_block_ranges(
        start_block=12_178_594,
        end_block=17_000_000,
        n=n_calls,
        range_size=range_size,
    )

    tests: typing.MutableMapping[str, rpc_bench.LoadTest] = {}
    for name, contract_address in contracts.items():
        calls = rpc_bench.create_calls_eth_get_logs(
            contract_address=contract_address,
            topics=[event_hashes['Transfer']],
            block_ranges=block_ranges,
        )
        tests[name] = {
            'url': url,
            'rates': rates,
            'duration': duration,
            'calls': calls,
        }

    return tests


def create_load_tests_eth_get_logs_by_block_range_size(
    url: str,
    rates: typing.Sequence[int],
    duration: int,
    range_sizes: typing.Sequence[int],
) -> typing.Mapping[str, rpc_bench.LoadTest]:
    """test: tiny vs small vs medium vs large block ranges"""

    n_calls = rpc_bench.estimate_call_count(rates=rates, duration=duration)

    tests: typing.MutableMapping[str, rpc_bench.LoadTest] = {}
    for range_size in range_sizes:
        block_ranges = rpc_bench.choose_random_block_ranges(
            start_block=12_178_594,
            end_block=17_000_000,
            n=n_calls,
            range_size=range_size,
        )
        calls = rpc_bench.create_calls_eth_get_logs(
            contract_address=contracts['USDC'],
            topics=[event_hashes['Transfer']],
            block_ranges=block_ranges,
        )
        name = str(range_size) + '_blocks'
        tests[name] = {
            'url': url,
            'rates': rates,
            'duration': duration,
            'calls': calls,
        }

    return tests


def create_load_tests_eth_get_logs_by_block_age(
    url: str,
    rates: typing.Sequence[int],
    duration: int,
    block_bounds: typing.Mapping[str, tuple[int, int]],
) -> typing.Mapping[str, rpc_bench.LoadTest]:
    """test old vs new blocks"""

    n_calls = rpc_bench.estimate_call_count(rates=rates, duration=duration)

    tests: typing.MutableMapping[str, rpc_bench.LoadTest] = {}
    for name, (start_block, end_block) in block_bounds.items():
        block_ranges = rpc_bench.choose_random_block_ranges(
            start_block=start_block,
            end_block=end_block,
            n=n_calls,
            range_size=100,
        )
        calls = rpc_bench.create_calls_eth_get_logs(
            contract_address=contracts['USDC'],
            topics=[event_hashes['Transfer']],
            block_ranges=block_ranges,
        )
        tests[name] = {
            'url': url,
            'rates': rates,
            'duration': duration,
            'calls': calls,
        }

    return tests

