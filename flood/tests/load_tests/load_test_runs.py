from __future__ import annotations

import typing

import flood
from flood import user_io
from flood import spec
from . import vegeta

if typing.TYPE_CHECKING:
    import multiprocessing


def run_load_tests(
    *,
    node: spec.NodeShorthand | None = None,
    nodes: spec.NodesShorthand | None = None,
    test: spec.LoadTest | spec.TestGenerationParameters | None = None,
    tests: typing.Mapping[str, spec.LoadTest | spec.TestGenerationParameters]
    | None = None,
    verbose: bool | int = False,
    include_deep_output: typing.Sequence[spec.DeepOutput] | None = None,
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
        'colour': flood.user_io.styles['content'],
        # 'disable': not verbose,
        'disable': True,
    }

    results = {}

    # case: single node and single test
    if node is not None and test is not None:
        results[node['name']] = schedule_load_test(
            node=node,
            test=test,
            include_deep_output=include_deep_output,
        )

    # case: single node and multiple tests
    elif node is not None and tests is not None:
        for name, each_test in tqdm.tqdm(tests.items(), **pbar):
            results[name] = schedule_load_test(
                node=node,
                verbose=verbose,
                test=each_test,
                include_deep_output=include_deep_output,
            )

    # case: multiple nodes and single tests
    elif nodes is not None and test is not None:
        for name, nd in tqdm.tqdm(nodes.items(), **pbar):
            results[name] = schedule_load_test(
                node=nd,
                verbose=verbose,
                test=test,
                include_deep_output=include_deep_output,
            )

    # case: multiple nodes and multiple tests
    elif nodes is not None and tests is not None:
        for node_name, node in nodes.items():
            for test_name, test in tests.items():
                results[node_name + '__' + test_name] = schedule_load_test(
                    node=node,
                    verbose=verbose,
                    test=test,
                    include_deep_output=include_deep_output,
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
            if process.exitcode != 0:
                import sys

                sys.exit()
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
    test: spec.LoadTest | spec.TestGenerationParameters,
    verbose: bool | int = False,
    include_deep_output: typing.Sequence[spec.DeepOutput] | None = None,
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
                verbose=verbose,
                include_deep_output=include_deep_output,
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
            verbose=verbose,
            include_deep_output=include_deep_output,
            _pbar_kwargs=_pbar_kwargs,
        )


def run_load_test(
    *,
    node: spec.NodeShorthand,
    test: spec.LoadTest | spec.TestGenerationParameters,
    verbose: bool | int = False,
    _pbar_kwargs: typing.Mapping[str, typing.Any] | None = None,
    _container: multiprocessing.Queue[str] | None = None,
    include_deep_output: typing.Sequence[spec.DeepOutput] | None = None,
) -> spec.LoadTestOutput | str:
    """run a load test against a single node"""

    # parse user_io
    node = user_io.parse_node(node)

    # run tests
    if node.get('remote') is None:
        result: spec.LoadTestOutput | str = _run_load_test_locally(
            node=node,
            test=test,
            verbose=verbose,
            _pbar_kwargs=_pbar_kwargs,
            include_deep_output=include_deep_output,
        )
    else:
        result = _run_load_test_remotely(
            node=node,
            test=test,
            verbose=verbose,
            _pbar_kwargs=_pbar_kwargs,
            include_deep_output=include_deep_output,
        )

    if _container is not None:
        if not isinstance(result, str):
            raise Exception('_container only supportted for remote testing')
        _container.put(result)

    return result


def _run_load_test_locally(
    *,
    node: spec.Node,
    test: spec.LoadTest | spec.TestGenerationParameters,
    verbose: bool | int = False,
    _pbar_kwargs: typing.Mapping[str, typing.Any] | None = None,
    include_deep_output: typing.Sequence[spec.DeepOutput] | None = None,
) -> spec.LoadTestOutput:
    """run a load test from local node"""

    if verbose:
        flood.user_io.print_timestamped('Running load test for ' + node['name'])

    # construct progress bar
    if _pbar_kwargs is None:
        _pbar_kwargs = {}
    tqdm = user_io.outputs._get_tqdm()
    tqdm_kwargs = dict(
        leave=False,
        desc='samples',
        position=1,
        colour=flood.user_io.styles['content'],
        # disable=not verbose,
        disable=True,
        **_pbar_kwargs,
    )

    use_test: spec.LoadTest
    if 'attacks' in test:
        use_test = test  # type: ignore
    else:
        use_test = flood.generate_test(**test)

    # perform tests
    results = []
    for attack in tqdm.tqdm(use_test['attacks'], **tqdm_kwargs):
        if verbose:
            flood.user_io.print_timestamped(
                'Running attack at rate = ' + str(attack['rate']) + ' rps'
            )

        result = vegeta.run_vegeta_attack(
            url=node['url'],
            calls=attack['calls'],
            duration=attack['duration'],
            rate=attack['rate'],
            vegeta_args=attack['vegeta_args'],
            verbose=verbose >= 2,
            include_deep_output=include_deep_output,
        )
        results.append(result)
        if verbose >= 2:
            print()

    # format output
    output_data: spec.LoadTestOutput = _list_of_maps_to_map_of_lists(results)  # type: ignore # noqa: E501

    # format deep output
    if include_deep_output is None or len(include_deep_output) == 0:
        for key in list(output_data.keys()):
            if key.startswith('deep_'):
                output_data[key] = None  # type: ignore
    else:
        output_data['deep_rpc_error_pairs'] = [
            result['deep_rpc_error_pairs'] for result in results
        ]

        # convert list of map of map into map of map of list
        categories: list[spec.ResponseCategory] = list(
            results[0]['deep_metrics'].keys()  # type: ignore
        )
        deep_metrics = {}
        for category in categories:
            deep_metrics[category] = _list_of_maps_to_map_of_lists(
                [result['deep_metrics'][category] for result in results]  # type: ignore # noqa: E501
            )
        output_data['deep_metrics'] = deep_metrics  # type: ignore

    return output_data


def _list_of_maps_to_map_of_lists(
    list_of_maps: typing.Sequence[typing.Mapping[typing.Any, typing.Any]]
) -> typing.Mapping[typing.Any, typing.Sequence[typing.Any]]:
    keys = list_of_maps[0].keys()
    return {key: [m[key] for m in list_of_maps] for key in keys}


def _run_load_test_remotely(
    *,
    node: spec.Node,
    test: spec.LoadTest | spec.TestGenerationParameters,
    verbose: bool | int = False,
    _pbar_kwargs: typing.Mapping[str, typing.Any] | None = None,
    include_deep_output: typing.Sequence[spec.DeepOutput] | None = None,
) -> str:
    """run a load test from local node"""

    import os
    import subprocess
    import sys
    import uuid
    import toolstr

    # parse node specification
    remote = node['remote']
    if remote is None:
        raise Exception('not a remote node')

    # check remote installation
    local_installation = flood.get_local_installation()
    remote_installation = flood.get_remote_installation(remote)
    local_flood_version = local_installation['flood_version']
    remote_flood_version = remote_installation['flood_version']
    remote_vegeta_path = remote_installation['vegeta_path']
    if remote_flood_version is None:
        raise Exception(
            'could not find flood installation on remote host ' + node['name']
        )
        sys.exit()
    if remote_vegeta_path is None:
        raise Exception(
            'could not find vegeta installation on remote host ' + node['name']
        )
        sys.exit()
    if local_flood_version != remote_flood_version:
        raise Exception(
            'local version of flood '
            + str(local_flood_version)
            + ' does not match remote version of flood '
            + remote_flood_version
        )

    # save call data, saving methods to preserve ordering in json
    job_id = str(uuid.uuid4())
    tempdir = '/tmp/flood__' + job_id
    os.makedirs(tempdir)
    test_parameters: flood.TestGenerationParameters
    if 'test_parameters' in test:
        test_parameters = test['test_parameters']  # type: ignore
    else:
        test_parameters = test
    flood.runners.single_runner.single_runner_io._save_single_run_test(
        test_name='',
        test_parameters=test_parameters,
        output_dir=tempdir,
    )

    # send call data to remote server
    if verbose:
        styles = flood.user_io.styles
        node_name = (
            toolstr.add_style('\[', styles['content'])
            + toolstr.add_style('node', styles['metavar'])
            + toolstr.add_style('=', styles['content'])
            + node['name']
            + toolstr.add_style(']', styles['content'])
        )
        flood.user_io.print_timestamped(
            node_name + ' Sending tests to remote node'
        )
    cmd = 'rsync -r ' + tempdir + ' ' + remote + ':' + os.path.dirname(tempdir)
    subprocess.call(cmd.split(' '), stderr=subprocess.DEVNULL)

    # initiate benchmarks
    if verbose:
        flood.user_io.print_timestamped(
            node_name + ' Executing test on remote node'
        )
    cmd_template = "ssh {host} bash -c 'source ~/.profile; python3 -m flood {test} {name}={url} --output {output} --no-figures {extra_kwargs}'"  # noqa: E501
    extra_kwargs = ''
    if include_deep_output is not None:
        if 'raw' in include_deep_output:
            extra_kwargs += ' --save-raw-output'
        if 'metrics' in include_deep_output:
            extra_kwargs += ' --deep-check'
    cmd = cmd_template.format(
        host=remote,
        name=node['name'],
        url=node['url'],
        test=tempdir,
        output=tempdir,
        extra_kwargs=extra_kwargs.lstrip(),
    )
    cmd = cmd.strip()
    subprocess.check_output(cmd.split(' '), stderr=subprocess.DEVNULL)

    # retrieve benchmark results
    if verbose:
        flood.user_io.print_timestamped(node_name + ' Retrieving results')
    results_path = os.path.join(tempdir, 'results.json')
    cmd = 'rsync ' + remote + ':' + results_path + ' ' + results_path
    subprocess.call(cmd.split(' '), stderr=subprocess.DEVNULL)

    return results_path

