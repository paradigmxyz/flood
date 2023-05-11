from __future__ import annotations

import typing

import rpc_bench


def generate_tests_eth_get_block_by_number_by_url(
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
        n=n_calls,
        random_seed=0,
        start_block=0,
        end_block=16_000_000,
    )

    calls = rpc_bench.generate_calls_eth_get_block_by_number(
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


def generate_tests_eth_get_block_by_hash_by_url(
    urls: typing.Sequence[str] | typing.Mapping[str, str],
    rates: typing.Sequence[int],
    duration: int,
) -> typing.Mapping[str, rpc_bench.LoadTest]:

    if isinstance(urls, list):
        urls = {url: url for url in urls}
    if not isinstance(urls, dict):
        raise Exception('could not convert urls')

    n_calls = rpc_bench.estimate_call_count(rates=rates, duration=duration)

    block_hashes = rpc_bench.generate_block_hashes(
        n=n_calls,
    )

    calls = rpc_bench.generate_calls_eth_get_block_by_hash(
        block_hashes=block_hashes,
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

