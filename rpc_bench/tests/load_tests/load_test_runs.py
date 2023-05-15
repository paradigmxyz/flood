from __future__ import annotations

import typing

from rpc_bench import user_io
from rpc_bench import spec
from . import load_test_construction
from . import vegeta


def run_load_tests(
    *,
    node: spec.NodeShorthand | None = None,
    nodes: spec.NodesShorthand | None = None,
    test: spec.LoadTest | None = None,
    tests: typing.Mapping[str, spec.LoadTest] | None = None,
    verbose: bool = False,
) -> typing.Mapping[str, spec.LoadTestOutput]:
    """run multiple load tests"""
    # parse user_io
    if (node is None) == (nodes is None):
        raise Exception('must specify either node or nodes')
    if (test is None) == (tests is None):
        raise Exception('must specify either test or tests')
    if node is not None:
        node = user_io.parse_node(node)
    if nodes is not None:
        nodes = user_io.parse_nodes(nodes)
    tqdm = user_io.outputs._get_tqdm()
    pbar = {'position': 0}

    # case: single node and single test
    if node is not None and test is not None:
        result = run_load_test(node=node, test=test)
        return {node['name']: result}

    # case: single node and multiple tests
    elif node is not None and tests is not None:
        results = {}
        for name, test in tqdm.tqdm(tests.items(), **pbar):
            results[name] = run_load_test(node=node, verbose=verbose, test=test)
        return results

    # case: multiple nodes and single tests
    elif nodes is not None and tests is not None:
        results = {}
        for name, nd in tqdm.tqdm(nodes.items(), **pbar):
            results[name] = run_load_test(node=nd, verbose=verbose, test=test)
        return results

    # case: multiple nodes and multiple tests
    elif nodes is not None and tests is not None:
        results = {}
        for node_name, node in nodes.items():
            for test_name, test in tests.items():
                results[node_name + '__' + test_name] = run_load_test(
                    node=node,
                    verbose=verbose,
                    test=test,
                )
        return results

    # case: invalid input
    else:
        raise Exception('invalid user_io')


def run_load_test(
    *,
    node: spec.NodeShorthand,
    test: spec.LoadTest | None = None,
    rates: typing.Sequence[int] | None = None,
    calls: typing.Sequence[typing.Any] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    verbose: bool = False,
    _pbar_kwargs: typing.Mapping[str, typing.Any] | None = None,
) -> spec.LoadTestOutput:
    """run a load test against a single node"""

    # parse user_io
    node = user_io.parse_node(node)
    if test is None:
        if (rates is None or calls is None):
            raise Exception('specify rates and calls')
        test = load_test_construction.construct_load_test(
            rates=rates,
            calls=calls,
            duration=duration,
            durations=durations,
            vegeta_kwargs=vegeta_kwargs,
        )

    # run tests
    if node.get('remote') is None:
        return _run_load_test_locally(
            node=node,
            test=test,
            verbose=verbose,
            _pbar_kwargs=_pbar_kwargs,
        )
    else:
        return _run_load_test_remotely(
            node=node,
            test=test,
            verbose=verbose,
            _pbar_kwargs=_pbar_kwargs,
        )


def _run_load_test_locally(
    *,
    node: spec.Node,
    test: spec.LoadTest | None,
    verbose: bool = False,
    _pbar_kwargs: typing.Mapping[str, typing.Any] | None = None,
) -> spec.LoadTestOutput:
    """run a load test from local node"""

    # construct progress bar
    if _pbar_kwargs is None:
        _pbar_kwargs = {}
    tqdm = user_io.outputs._get_tqdm()
    tqdm_kwargs = dict(leave=False, desc='samples', **_pbar_kwargs)

    # perform tests
    results = []
    for attack in tqdm.tqdm(test, **tqdm_kwargs):
        result = vegeta.run_vegeta_attack(
            url=node['url'],
            calls=attack['calls'],
            duration=attack['duration'],
            rate=attack['duration'],
            vegeta_kwargs=attack['vegeta_kwargs'],
            verbose=verbose >= 2,
        )
        results.append(result)
        if verbose:
            print()

    # format output
    keys = results[0].keys()
    return {key: [result[key] for result in results] for key in keys}  # type: ignore


def _run_load_test_remotely(
    *,
    node: spec.Node,
    test: spec.LoadTest | None,
    verbose: bool = False,
    _pbar_kwargs: typing.Mapping[str, typing.Any] | None = None,
) -> spec.LoadTestOutput:
    """run a load test from local node"""
    raise NotImplementedError()

