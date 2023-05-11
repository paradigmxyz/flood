from __future__ import annotations

import typing

import rpc_bench


def generate_tests_eth_get_code_by_url(
    urls: typing.Sequence[str] | typing.Mapping[str, str],
    rates: typing.Sequence[int],
    duration: int,
) -> typing.Mapping[str, rpc_bench.LoadTest]:
    if isinstance(urls, list):
        urls = {url: url for url in urls}
    if not isinstance(urls, dict):
        raise Exception('could not convert urls')

    n_calls = rpc_bench.estimate_call_count(rates=rates, duration=duration)

    block_numbers = rpc_bench.generate_block_numbers(
        start_block=10_000_000,
        end_block=16_000_000,
        n=n_calls,
        random_seed=0,
    )

    contract_addresses = rpc_bench.generate_contract_addresses(n_calls)
    calls = rpc_bench.generate_calls_eth_get_code(
        addresses=contract_addresses,
        block_numbers=block_numbers,
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


def generate_tests_eth_storage_at_by_url(
    urls: typing.Sequence[str] | typing.Mapping[str, str],
    rates: typing.Sequence[int],
    duration: int,
) -> typing.Mapping[str, rpc_bench.LoadTest]:
    if isinstance(urls, list):
        urls = {url: url for url in urls}
    if not isinstance(urls, dict):
        raise Exception('could not convert urls')

    n_calls = rpc_bench.estimate_call_count(rates=rates, duration=duration)

    block_numbers = rpc_bench.generate_block_numbers(
        start_block=10_000_000,
        end_block=16_000_000,
        n=n_calls,
        random_seed=0,
    )

    slots = rpc_bench.generate_slots(n_calls)
    calls = rpc_bench.generate_calls_eth_get_storage_at(
        slots=slots,
        block_numbers=block_numbers,
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


