from __future__ import annotations

import typing

import rpc_bench


def generate_tests_eth_get_transaction_by_hash(
    urls: typing.Sequence[str] | typing.Mapping[str, str],
    rates: typing.Sequence[int],
    duration: int,
) -> typing.Mapping[str, rpc_bench.LoadTest]:

    if isinstance(urls, list):
        urls = {url: url for url in urls}
    if not isinstance(urls, dict):
        raise Exception('could not convert urls')

    n_calls = rpc_bench.estimate_call_count(rates=rates, duration=duration)

    transaction_hashes = rpc_bench.generate_transaction_hashes(n_calls)
    calls = rpc_bench.generate_calls_eth_get_transaction_by_hash(
        transaction_hashes=transaction_hashes,
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


def generate_tests_eth_get_transaction_receipt(
    urls: typing.Sequence[str] | typing.Mapping[str, str],
    rates: typing.Sequence[int],
    duration: int,
) -> typing.Mapping[str, rpc_bench.LoadTest]:

    if isinstance(urls, list):
        urls = {url: url for url in urls}
    if not isinstance(urls, dict):
        raise Exception('could not convert urls')

    n_calls = rpc_bench.estimate_call_count(rates=rates, duration=duration)

    transaction_hashes = rpc_bench.generate_transaction_hashes(n_calls)
    calls = rpc_bench.generate_calls_eth_get_transaction_receipt(
        transaction_hashes=transaction_hashes,
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

