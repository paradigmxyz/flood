from __future__ import annotations

import typing

from rpc_bench import inputs
from rpc_bench import outputs
from rpc_bench import spec
from . import vegeta


def run_load_tests(
    tests: typing.Mapping[str, spec.LoadTest],
) -> typing.Mapping[str, spec.LoadTestOutput]:
    results = {}
    tqdm = outputs._get_tqdm()
    for name, test in tqdm.tqdm(
        tests.items(), desc='nodes', leave=False, position=0
    ):
        results[name] = run_load_test(
            url=test['url'],
            rates=test['rates'],
            calls=test['calls'],
            duration=test['duration'],
            verbose=False,
            tqdm_position=1,
        )

    return results


def run_load_test(
    *,
    url: str,
    rates: typing.Sequence[int],
    calls: typing.Sequence[typing.Any],
    duration: int,
    verbose: bool = True,
    tqdm_position: int = 0,
) -> spec.LoadTestOutput:

    # check if url is ctc alias
    alias_url = inputs.get_ctc_alias_url(url)
    if alias_url is not None:
        url = alias_url

    # validate inputs
    if len(rates) == 0:
        raise Exception('must specify at least one rate')

    # partition calls into tests
    calls_iter = iter(calls)
    tests_calls = []
    for rate in rates:
        n_test_calls = rate * duration
        test_calls = []
        for i in range(n_test_calls):
            test_calls.append(next(calls_iter))
        tests_calls.append(test_calls)

    # perform tests
    reports = []
    tqdm = outputs._get_tqdm()
    for rate, test_calls in tqdm.tqdm(
        list(zip(rates, tests_calls)),
        leave=False,
        desc='rates',
        position=tqdm_position,
    ):
        report = vegeta.run_vegeta_attack(
            calls=test_calls,
            url=url,
            duration=duration,
            rate=rate,
        )
        reports.append(report)

    # format output
    return {  # type: ignore
        key: [report[key] for report in reports]  # type: ignore
        for key in reports[0].keys()
    }

