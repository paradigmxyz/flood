from __future__ import annotations

import typing

import flood
from flood import user_io
from flood import spec
from . import load_test_construction
from . import vegeta

if typing.TYPE_CHECKING:
    import multiprocessing


def run_load_tests(
    *,
    node: spec.NodeShorthand | None = None,
    nodes: spec.NodesShorthand | None = None,
    test: spec.LoadTest | None = None,
    tests: typing.Mapping[str, spec.LoadTest] | None = None,
    verbose: bool | int = False,
    include_raw_output: bool = False,
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
        nodes = user_io.parse_nodes(nodes, request_metadata=False)
    tqdm = user_io.outputs._get_tqdm()
    pbar = {
        'leave': False,
        'desc': 'nodes',
        'position': 0,
        'colour': flood.styles['content'],
        # 'disable': not verbose,
        'disable': True,
    }

    results = {}

    # case: single node and single test
    if node is not None and test is not None:
        results[node['name']] = schedule_load_test(
            node=node,
            test=test,
            include_raw_output=include_raw_output,
        )

    # case: single node and multiple tests
    elif node is not None and tests is not None:
        for name, test in tqdm.tqdm(tests.items(), **pbar):
            results[name] = schedule_load_test(
                node=node,
                verbose=verbose,
                test=test,
                include_raw_output=include_raw_output,
            )

    # case: multiple nodes and single tests
    elif nodes is not None and test is not None:
        for name, nd in tqdm.tqdm(nodes.items(), **pbar):
            results[name] = schedule_load_test(
                node=nd,
                verbose=verbose,
                test=test,
                include_raw_output=include_raw_output,
            )

    # case: multiple nodes and multiple tests
    elif nodes is not None and tests is not None:
        for node_name, node in nodes.items():
            for test_name, test in tests.items():
                results[node_name + '__' + test_name] = schedule_load_test(
                    node=node,
                    verbose=verbose,
                    test=test,
                    include_raw_output=include_raw_output,
                )

    # case: invalid input
    else:
        raise Exception('invalid user_io')

    # join any multiprocessing results
    joined = {}
    for name, result in results.items():
        if isinstance(result, dict):
            joined[name] = result
        elif isinstance(result, tuple):
            process, queue = result
            process.join()
            results_path = queue.get()
            with open(results_path, 'r') as f:
                import json

                test_results: spec.SingleRunResultsPayload = json.load(f)
                joined[name] = test_results['results'][name]
        else:
            raise Exception('invalid result type')

    return joined


def schedule_load_test(
    *,
    node: spec.NodeShorthand,
    test: spec.LoadTest | None = None,
    rates: typing.Sequence[int] | None = None,
    calls: typing.Sequence[typing.Any] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    verbose: bool | int = False,
    include_raw_output: bool = False,
    _pbar_kwargs: typing.Mapping[str, typing.Any] | None = None,
) -> (
    spec.LoadTestOutput
    | str
    | tuple[multiprocessing.Process, multiprocessing.Queue[str]]
):
    """runs local tests synchronously, remote tests asynchronously"""

    node = user_io.parse_node(node)
    if node['remote'] is not None:
        import multiprocessing

        queue: multiprocessing.Queue[str] = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=run_load_test,
            kwargs=dict(
                node=node,
                test=test,
                rates=rates,
                calls=calls,
                duration=duration,
                durations=durations,
                vegeta_kwargs=vegeta_kwargs,
                verbose=verbose,
                include_raw_output=include_raw_output,
                _pbar_kwargs=_pbar_kwargs,
                _container=queue,
            ),
        )
        process.start()
        return (process, queue)
    else:
        return run_load_test(
            node=node,
            test=test,
            rates=rates,
            calls=calls,
            duration=duration,
            durations=durations,
            vegeta_kwargs=vegeta_kwargs,
            verbose=verbose,
            include_raw_output=include_raw_output,
            _pbar_kwargs=_pbar_kwargs,
        )


def run_load_test(
    *,
    node: spec.NodeShorthand,
    test: spec.LoadTest | None = None,
    rates: typing.Sequence[int] | None = None,
    calls: typing.Sequence[typing.Any] | None = None,
    duration: int | None = None,
    durations: typing.Sequence[int] | None = None,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    verbose: bool | int = False,
    _pbar_kwargs: typing.Mapping[str, typing.Any] | None = None,
    _container: multiprocessing.Queue[str] | None = None,
    include_raw_output: bool = False,
) -> spec.LoadTestOutput | str:
    """run a load test against a single node"""

    # parse user_io
    node = user_io.parse_node(node)
    if test is None:
        if rates is None or calls is None:
            raise Exception('specify rates and calls')
        test = load_test_construction.create_load_test(
            rates=rates,
            calls=calls,
            duration=duration,
            durations=durations,
            vegeta_kwargs=vegeta_kwargs,
        )

    # run tests
    if node.get('remote') is None:
        result: spec.LoadTestOutput | str = _run_load_test_locally(
            node=node,
            test=test,
            verbose=verbose,
            _pbar_kwargs=_pbar_kwargs,
            include_raw_output=include_raw_output,
        )
    else:
        result = _run_load_test_remotely(
            node=node,
            test=test,
            verbose=verbose,
            _pbar_kwargs=_pbar_kwargs,
            include_raw_output=include_raw_output,
        )

    if _container is not None:
        if not isinstance(result, str):
            raise Exception('_container only supportted for remote testing')
        _container.put(result)

    return result


def _run_load_test_locally(
    *,
    node: spec.Node,
    test: spec.LoadTest | None,
    verbose: bool | int = False,
    _pbar_kwargs: typing.Mapping[str, typing.Any] | None = None,
    include_raw_output: bool = False,
) -> spec.LoadTestOutput:
    """run a load test from local node"""
    import datetime
    import toolstr

    if verbose:
        dt = datetime.datetime.now()
        if dt.microsecond >= 500_000:
            dt = dt + datetime.timedelta(
                microseconds=1_000_000 - dt.microsecond
            )
        else:
            dt = dt - datetime.timedelta(microseconds=dt.microsecond)
        timestamp = (
            toolstr.add_style('\[', flood.styles['content'])
            + toolstr.add_style(str(dt), flood.styles['metavar'])
            + toolstr.add_style(']', flood.styles['content'])
        )
        toolstr.print(timestamp + ' Running load test for ' + node['name'])

    # construct progress bar
    if _pbar_kwargs is None:
        _pbar_kwargs = {}
    tqdm = user_io.outputs._get_tqdm()
    tqdm_kwargs = dict(
        leave=False,
        desc='samples',
        position=1,
        colour=flood.styles['content'],
        # disable=not verbose,
        disable=True,
        **_pbar_kwargs,
    )

    # perform tests
    results = []
    for attack in tqdm.tqdm(test, **tqdm_kwargs):
        if verbose:
            dt = datetime.datetime.now()
            if dt.microsecond >= 500_000:
                dt = dt + datetime.timedelta(
                    microseconds=1_000_000 - dt.microsecond
                )
            else:
                dt = dt - datetime.timedelta(microseconds=dt.microsecond)
            timestamp = (
                toolstr.add_style('\[', flood.styles['content'])
                + toolstr.add_style(str(dt), flood.styles['metavar'])
                + toolstr.add_style(']', flood.styles['content'])
            )
            toolstr.print(
                timestamp
                + ' Running attack at rate = '
                + str(attack['rate'])
                + ' rps'
            )

        result = vegeta.run_vegeta_attack(
            url=node['url'],
            calls=attack['calls'],
            duration=attack['duration'],
            rate=attack['rate'],
            vegeta_kwargs=attack['vegeta_kwargs'],
            verbose=verbose >= 2,
            include_raw_output=include_raw_output,
        )
        results.append(result)
        if verbose >= 2:
            print()

    # format output
    keys = results[0].keys()
    return {key: [result[key] for result in results] for key in keys}  # type: ignore # noqa: E501


def _run_load_test_remotely(
    *,
    node: spec.Node,
    test: spec.LoadTest,
    verbose: bool | int = False,
    _pbar_kwargs: typing.Mapping[str, typing.Any] | None = None,
    include_raw_output: bool = False,
) -> str:
    """run a load test from local node"""

    import os
    import subprocess
    import uuid
    import toolstr

    # parse node specification
    remote = node['remote']
    if remote is None:
        raise Exception('not a remote node')

    # save call data, saving methods to preserve ordering in json
    job_id = str(uuid.uuid4())
    tempdir = '/tmp/flood__' + job_id
    os.makedirs(tempdir)
    flood.runners.single_runner.single_runner_io._save_single_run_test(
        test_name='',
        test=test,
        output_dir=tempdir,
    )

    # send call data to remote server
    if verbose:
        import datetime

        dt = datetime.datetime.now()
        if dt.microsecond >= 500_000:
            dt = dt + datetime.timedelta(
                microseconds=1_000_000 - dt.microsecond
            )
        else:
            dt = dt - datetime.timedelta(microseconds=dt.microsecond)
        timestamp = (
            toolstr.add_style('\[', flood.styles['content'])
            + toolstr.add_style(str(dt), flood.styles['metavar'])
            + toolstr.add_style(']', flood.styles['content'])
        )
        node_name = (
            toolstr.add_style('\[', flood.styles['content'])
            + toolstr.add_style('node', flood.styles['metavar'])
            + toolstr.add_style('=', flood.styles['content'])
            + node['name']
            + toolstr.add_style(']', flood.styles['content'])
        )
        toolstr.print(
            timestamp + ' ' + node_name + ' Sending tests to remote node'
        )
    cmd = 'rsync -r ' + tempdir + ' ' + remote + ':' + os.path.dirname(tempdir)
    subprocess.call(cmd.split(' '), stderr=subprocess.DEVNULL)

    # initiate benchmarks
    if verbose:
        dt = datetime.datetime.now()
        if dt.microsecond >= 500_000:
            dt = dt + datetime.timedelta(
                microseconds=1_000_000 - dt.microsecond
            )
        else:
            dt = dt - datetime.timedelta(microseconds=dt.microsecond)
        timestamp = (
            toolstr.add_style('\[', flood.styles['content'])
            + toolstr.add_style(str(dt), flood.styles['metavar'])
            + toolstr.add_style(']', flood.styles['content'])
        )
        toolstr.print(
            timestamp + ' ' + node_name + ' Executing test on remote node'
        )
    cmd_template = "ssh {host} bash -c 'source ~/.profile; python3 -m flood {test} {name}={url} --output {output} --no-figures {extra_kwargs}'"  # noqa: E501
    if include_raw_output:
        extra_kwargs = '--save-raw-output'
    else:
        extra_kwargs = ''
    cmd = cmd_template.format(
        host=remote,
        name=node['name'],
        url=node['url'],
        test=tempdir,
        output=tempdir,
        extra_kwargs=extra_kwargs,
    )
    cmd = cmd.strip()
    subprocess.check_output(cmd.split(' '), stderr=subprocess.DEVNULL)

    # retrieve benchmark results
    if verbose:
        dt = datetime.datetime.now()
        if dt.microsecond >= 500_000:
            dt = dt + datetime.timedelta(
                microseconds=1_000_000 - dt.microsecond
            )
        else:
            dt = dt - datetime.timedelta(microseconds=dt.microsecond)
        timestamp = (
            toolstr.add_style('\[', flood.styles['content'])
            + toolstr.add_style(str(dt), flood.styles['metavar'])
            + toolstr.add_style(']', flood.styles['content'])
        )
        toolstr.print(timestamp + ' ' + node_name + ' Retrieving results')
    results_path = os.path.join(tempdir, 'results.json')
    cmd = 'rsync ' + remote + ':' + results_path + ' ' + results_path
    subprocess.call(cmd.split(' '), stderr=subprocess.DEVNULL)

    return results_path

