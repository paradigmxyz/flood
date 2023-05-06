from __future__ import annotations

import json
import typing

import requests

from . import rpc_methods
from . import spec
from . import verbosity


def run_latency_benchmark(
    *,
    nodes: spec.NodesShorthand,
    methods: typing.Sequence[str] | None,
    samples: int | None = None,
    calls: spec.MethodCalls | None = None,
    calls_file: str | None = None,
    verbose: bool = True,
    output_file: str | None = None,
    random_seed: int | None = None,
) -> None:
    """run latency benchmark on specified nodes and methods"""

    # parse inputs
    if not isinstance(nodes, dict):
        nodes = _parse_nodes(nodes)

    # create calls
    if calls is None:
        calls = rpc_methods.create_calls(
            methods=methods,
            samples=samples,
            random_seed=random_seed,
            calls_file=calls_file,
        )

    # print prelude
    if verbose:
        verbosity._print_benchmark_prelude(
            nodes=nodes,
            methods=methods,
            samples=samples,
            random_seed=random_seed,
            calls=calls,
            output_file=output_file,
        )

    # perform calls
    latencies = _perform_calls(nodes=nodes, calls=calls, verbose=verbose)

    # print summary
    if verbose:
        verbosity._print_benchmark_summary(latencies=latencies, calls=calls)

    # output file
    if output_file is not None:
        summary: spec.LatencyBenchmarkResults = {
            'nodes': nodes,
            'methods': list(calls.keys()),
            'samples': samples,
            'calls': calls,
            'latencies': latencies,
        }
        with open(output_file, 'w') as f:
            json.dump(summary, f)


def _parse_nodes(nodes: spec.NodesShorthand) -> typing.Mapping[str, spec.Node]:
    """parse given nodes according to input specification"""
    new_nodes: typing.MutableMapping[str, spec.Node] = {}
    if isinstance(nodes, list):
        for node in nodes:
            new_node = _parse_node(node)
            new_nodes[new_node['name']] = new_node
    elif isinstance(nodes, dict):
        for key, value in nodes.items():
            new_nodes[key] = value
    else:
        raise Exception('invalid format for nodes')
    return new_nodes


def _parse_node(node: str | spec.Node) -> spec.Node:
    prefixes = ['http', 'https', 'ws', 'wss']

    if isinstance(node, dict):
        return node
    elif isinstance(node, str):
        # parse name
        if '=' in node:
            name, url = node.split('=')
        else:
            name = node
            url = node

        # parse remote and url
        if ':' in url:
            head, tail = url.split(':', 1)
            if head in prefixes:
                remote = None
                url = head + ':' + tail
            else:
                if tail.split('/')[0].isdecimal():
                    remote = None
                    url = url
                else:
                    remote = head
                    url = tail
        else:
            remote = None

        # add missing prefix
        if not any(url.startswith(prefix) for prefix in prefixes):
            if (
                url.startswith('localhost')
                or url.startswith('0.0.0.0')
                or url.startswith('127.0.0.1')
            ):
                url = 'http://' + url
            else:
                url = 'https://' + url

        return {
            'name': name,
            'url': url,
            'remote': remote,
        }

    else:
        raise Exception('invalid node format')


def _perform_calls(
    nodes: typing.Mapping[str, spec.Node],
    calls: spec.MethodCalls,
    verbose: bool,
) -> spec.NodeMethodLatencies:
    """perform RPC calls"""

    import tqdm

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
    latencies: spec.NodeMethodLatencies = {
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

