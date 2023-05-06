from __future__ import annotations

import json
import typing

import requests

from rpc_bench import spec
from rpc_bench import rpc_methods
from rpc_bench import verbosity


def run_latency_benchmark(
    *,
    nodes: typing.Sequence[str] | typing.Mapping[str, str],
    methods: typing.Sequence[str] | None,
    samples: int | None = None,
    verbose: bool = True,
    output_file: str | None = None,
    random_seed: int | None = None,
) -> None:
    """run latency benchmark on specified nodes and methods"""

    # parse inputs
    if not isinstance(nodes, dict):
        nodes = _parse_nodes(nodes)
    if samples is None:
        samples = 1
    if methods is None:
        methods = rpc_methods.get_all_methods()
    if random_seed is None:
        random_seed = 0

    # print prelude
    if verbose:
        verbosity._print_benchmark_prelude(
            nodes=nodes,
            methods=methods,
            samples=samples,
            output_file=output_file,
            random_seed=random_seed,
        )

    # create calls
    calls = rpc_methods.create_calls(
        methods=methods, samples=samples, random_seed=random_seed
    )

    # perform calls
    latencies = _perform_calls(
        nodes=nodes, methods=methods, calls=calls, verbose=verbose
    )

    # print summary
    if verbose:
        verbosity._print_benchmark_summary(latencies=latencies, calls=calls)

    # output file
    if output_file is not None:
        summary: spec.LatencyBenchmarkResults = {
            'nodes': nodes,
            'methods': methods,
            'samples': samples,
            'calls': calls,
            'latencies': latencies,
        }
        with open(output_file, 'w') as f:
            json.dump(summary, f)


def _parse_nodes(
    nodes: typing.Sequence[str] | typing.Mapping[str, str]
) -> typing.Mapping[str, str]:
    """parse given nodes according to input specification"""
    if isinstance(nodes, list):
        new_nodes = {}
        for node in nodes:
            if '=' in node:
                name, url = node.split('=')
                new_nodes[name] = url
            else:
                new_nodes[name] = url
        return new_nodes
    elif isinstance(nodes, dict):
        return nodes
    else:
        raise Exception('invalid format for nodes')


def _perform_calls(
    nodes: typing.Mapping[str, str],
    methods: typing.Sequence[str],
    calls: spec.MethodCalls,
    verbose: bool,
) -> spec.NodeMethodLatencies:
    """perform RPC calls"""

    import tqdm

    # print prelude and get progress bars
    if verbose:
        start_time = verbosity._print_call_prelude()
    node_bar, method_bar, sample_bar = verbosity._get_progress_bars(verbose)

    # specify headers
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'rpc_bench',
    }

    # perform calls
    latencies: spec.NodeMethodLatencies = {
        name: {method: [] for method in methods} for name in nodes.keys()
    }
    for name, url in tqdm.tqdm(nodes.items(), **node_bar):
        for method in tqdm.tqdm(methods, **method_bar):
            for call in tqdm.tqdm(calls[method], **sample_bar):
                response = requests.post(
                    url=_get_url(url),
                    data=json.dumps(call),
                    headers=headers,
                )
                latency = response.elapsed.total_seconds()
                latencies[name][method].append(latency)  # type: ignore

    # print summary
    if verbose:
        verbosity._print_call_summary(start_time)

    return latencies


def _get_url(node: str) -> str:
    """add http or https to hostname as needed"""
    if not node.startswith('http'):
        if (
            node.startswith('localhost')
            or node.startswith('0.0.0.0')
            or node.startswith('127.0.0.1')
        ):
            return 'http://' + node
        else:
            return 'https://' + node
    else:
        return node

