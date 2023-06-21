from __future__ import annotations

import typing

import flood
from . import single_runner_io
from . import single_runner_summary


def _run_single(
    *,
    test_name: str,
    rerun_of: str | None = None,
    test: flood.LoadTest | None = None,
    nodes: flood.NodesShorthand,
    random_seed: flood.RandomSeed | None = None,
    rates: typing.Sequence[int] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    mode: flood.LoadTestMode | None = None,
    vegeta_kwargs: flood.VegetaKwargsShorthand | None = None,
    dry: bool,
    output_dir: str | None = None,
    figures: bool,
    metrics: typing.Sequence[str] | None = None,
    verbose: bool | int,
    include_raw_output: bool = False,
    deep_check: bool = False,
) -> None:
    if deep_check:
        include_raw_output = True

    # get test parameters
    rates, durations, vegeta_kwargs = _get_single_test_parameters(
        test=test,
        rates=rates,
        duration=duration,
        durations=durations,
        mode=mode,
    )

    # print preamble
    if verbose:
        single_runner_summary._print_single_run_preamble_copy(
            test_name=test_name,
            rerun_of=rerun_of,
            rates=rates,
            durations=durations,
            vegeta_kwargs=vegeta_kwargs,
            output_dir=output_dir,
        )

    # parse nodes
    nodes = flood.parse_nodes(nodes, verbose=verbose, request_metadata=True)

    # generate test and save to disk
    if test is None:
        test = flood.generate_test(
            test_name=test_name,
            rates=rates,
            durations=durations,
            vegeta_kwargs=vegeta_kwargs,
            network=flood.parse_nodes_network(nodes),
            random_seed=random_seed,
            output_dir=output_dir,
        )

    # skip dry run
    if dry:
        print()
        print('[dry run, exitting]')
        return

    # run tests
    if verbose:
        single_runner_summary._print_run_start()
    results = flood.run_load_tests(
        nodes=nodes,
        test=test,
        verbose=verbose,
        include_raw_output=include_raw_output,
    )

    # output results to file
    if output_dir is not None:
        single_runner_io._save_single_run_results(
            output_dir=output_dir,
            test=test,
            nodes=nodes,
            results=results,
            figures=figures,
            test_name=test_name,
        )

    # perform deep check
    if deep_check:
        _perform_deep_check(results, verbose=verbose)

    # print summary
    if verbose:
        single_runner_summary._print_single_run_conclusion_copy(
            output_dir=output_dir,
            results=results,
            metrics=metrics,
            verbose=verbose,
            figures=figures,
        )


#
# # helper functions
#


def _perform_deep_check(
    results: typing.Mapping[str, flood.LoadTestOutput],
    verbose: bool | int = False,
) -> None:
    """
    check that responses for each success are
    1) well-formed json
    and 2) error = None
    """
    import base64
    import json

    errors = False

    raw_output = flood.load_single_run_raw_output(results=results)
    for result_name, result in raw_output.items():
        for status_code, response in zip(
            result['status_code'], result['response'].to_list()
        ):
            if status_code == 200:
                try:
                    decoded = json.loads(base64.b64decode(response))
                    if decoded.get('result') is None:
                        errors = True
                except Exception:
                    errors = True

            if errors:
                break
        if errors:
            break

    if verbose:
        if errors:
            print()
            print('[deep check passed]')
        else:
            print('[deep check failed]')

    if errors:
        raise Exception('some calls that were reported successful had bad data')


def _get_single_test_parameters(
    test: flood.LoadTest | None = None,
    rates: typing.Sequence[int] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    mode: flood.LoadTestMode | None = None,
    vegeta_kwargs: flood.VegetaKwargsShorthand | None = None,
) -> tuple[
    typing.Sequence[int],
    typing.Sequence[int],
    flood.VegetaKwargsShorthand | None,
]:
    if test is not None:
        test_data = flood.parse_test_data(test=test)
        rates = test_data['rates']
        durations = test_data['durations']
        vegeta_kwargs = test_data['vegeta_kwargs']
    else:
        rates, durations = flood.generate_timings(
            rates=rates,
            duration=duration,
            durations=durations,
            mode=mode,
        )
    return rates, durations, vegeta_kwargs

