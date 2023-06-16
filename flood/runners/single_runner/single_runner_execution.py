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
) -> None:
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
        return

    # run tests
    if verbose:
        single_runner_summary._print_run_start()
    results = flood.run_load_tests(nodes=nodes, test=test, verbose=verbose)

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

