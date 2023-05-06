from __future__ import annotations

import typing

from . import spec
from . import verbosity


def execute_calls(
    nodes: typing.Mapping[str, spec.Node],
    calls: spec.MethodCalls,
    verbose: bool,
) -> spec.NodesMethodLatencies:
    """perform RPC calls"""
    # local calls
    local_nodes = {k: v for k, v in nodes.items() if v['remote'] is None}
    local_latencies = _execute_local_calls(
        nodes=local_nodes, calls=calls, verbose=verbose
    )

    # remote calls
    remote_nodes = {k: v for k, v in nodes.items() if v['remote'] is not None}
    remote_latencies = _execute_remote_calls(
        nodes=remote_nodes, calls=calls, verbose=verbose
    )

    return dict(local_latencies, **remote_latencies)


def _execute_local_calls(
    nodes: typing.Mapping[str, spec.Node],
    calls: spec.MethodCalls,
    verbose: bool,
) -> spec.NodesMethodLatencies:
    """perform local RPC calls"""

    import json
    import requests
    import tqdm

    if len(nodes) == 0:
        return {}

    # print prelude and get progress bars
    if verbose:
        start_time = verbosity._print_call_prelude()
    node_bar, method_bar, sample_bar = verbosity._get_progress_bars(
        nodes=nodes, verbose=verbose
    )

    # specify headers
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'rpc_bench',
    }

    # perform calls
    methods = list(calls.keys())
    latencies: spec.NodesMethodLatencies = {
        name: {method: [] for method in methods} for name in nodes.keys()
    }
    for name, node in tqdm.tqdm(nodes.items(), **node_bar):
        for method in tqdm.tqdm(methods, **method_bar):
            for call in tqdm.tqdm(calls[method], **sample_bar):
                response = requests.post(
                    url=node['url'],
                    data=json.dumps(call),
                    headers=headers,
                )
                latency = response.elapsed.total_seconds()
                latencies[name][method].append(latency)  # type: ignore

    # print summary
    if verbose:
        verbosity._print_call_summary(start_time)

    return latencies


def _execute_remote_calls(
    nodes: typing.Mapping[str, spec.Node],
    calls: spec.MethodCalls,
    verbose: bool,
) -> spec.NodesMethodLatencies:
    """perform remote RPC calls"""
    latencies: typing.MutableMapping[
        str,
        typing.Mapping[str, typing.Sequence[float]],
    ]
    latencies = {}
    for name, node in nodes.items():
        remote = node['remote']
        if remote is None:
            raise Exception('not a remote node')
        result = _execute_node_remote_calls(node=node, calls=calls)
        latencies[name] = result
    return latencies


def _execute_node_remote_calls(
    node: spec.Node, calls: spec.MethodCalls
) -> spec.NodeMethodLatencies:
    """perform remote RPC calls on particular node"""

    import json
    import os
    import subprocess
    import uuid

    # parse node specification
    remote = node['remote']
    if remote is None:
        raise Exception('not a remote node')

    # save call data, saving methods to preserve ordering in json
    job_id = str(uuid.uuid4())
    tempdir = '/tmp/rpc_bench__' + job_id
    os.makedirs(tempdir)
    calls_path = os.path.join(tempdir, 'calls.json')
    calls_data = {'methods': list(calls.keys()), 'calls': calls}
    with open(calls_path, 'w') as f:
        json.dump(calls_data, f)

    # send call data to remote server
    cmd = 'ssh {host} mkdir {tempdir}'.format(host=remote, tempdir=tempdir)
    subprocess.call(cmd.split(' '), stderr=subprocess.DEVNULL)
    cmd = 'rsync ' + calls_path + ' ' + remote + ':' + calls_path
    subprocess.call(cmd.split(' '), stderr=subprocess.DEVNULL)

    # initiate benchmarks
    results_path = os.path.join(tempdir, 'results.json')
    cmd = 'ssh {host} python3 -m rpc_bench {url} --calls {calls_path} --output {output}'.format(
        host=remote,
        url=node['url'],
        calls_path=calls_path,
        output=results_path,
    )
    subprocess.check_output(cmd.split(' '), stderr=subprocess.DEVNULL)

    # retrieve benchmark results
    cmd = 'rsync ' + remote + ':' + results_path + ' ' + results_path
    subprocess.call(cmd.split(' '), stderr=subprocess.DEVNULL)

    # return results
    with open(results_path, 'r') as f:
        results: spec.LatencyBenchmarkResults = json.load(f)
        return results['latencies'][node['url']]

