from __future__ import annotations

import typing

from . import spec
from . import verbosity
from .external_utils import vegeta


#
# # loadtest creation
#

def estimate_total_test_calls(
    rates: typing.Sequence[int],
    duration: int = 5,
    *,
    n_repeats: int | None = None,
) -> int:
    n_calls = sum(duration * rate for rate in rates)
    if n_repeats is not None:
        n_calls *= n_repeats
    return n_calls


def create_loadtests(
    url: str | None = None,
    urls: typing.Sequence[str] | None = None,
    calls: typing.Sequence[spec.Call] | None = None,
    calls_lists: typing.Sequence[typing.Sequence[spec.Call]] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | typing.Mapping[str, int] | None = None,
    rates: int | None = None,
    rates_list: typing.Sequence[int] | typing.Mapping[str, int] | None = None,
) -> typing.Mapping[str, spec.LoadTest]:
    raise NotADirectoryError()


#
# # loadtest running
#

def run_loadtests(
    tests: typing.Mapping[str, spec.LoadTest],
) -> typing.Mapping[str, spec.LoadTestOutput]:
    results = {}
    tqdm = verbosity._get_tqdm()
    for name, test in tqdm.tqdm(tests, desc='nodes', leave=False, position=0):
        results[name] = run_loadtest(
            url=test['url'],
            rates=test['rates'],
            calls=test['calls'],
            duration=test['duration'],
            verbose=False,
            tqdm_position=1,
        )

    return results


def run_loadtest(
    *,
    url: str,
    rates: typing.Sequence[int],
    calls: typing.Sequence[typing.Any],
    duration: int,
    verbose: bool = True,
    tqdm_position: int = 0,
) -> spec.LoadTestOutput:
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
    tqdm = verbosity._get_tqdm()
    for rate, test_calls in tqdm.tqdm(
        list(zip(rates, tests_calls)),
        leave=False,
        desc='rates',
        position=tqdm_position,
    ):
        report = vegeta.run_loadtest_datum(
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

