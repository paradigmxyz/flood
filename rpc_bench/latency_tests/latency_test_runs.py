from __future__ import annotations

import json
import typing

from rpc_bench import inputs
from rpc_bench import spec
from . import call_creation
from . import latency_test_execution
from . import latency_test_outputs


def run_latency_test(
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

    import datetime
    import time

    # parse inputs
    if not isinstance(nodes, dict):
        nodes = inputs.parse_nodes(nodes)
    start_time = datetime.datetime.fromtimestamp(int(time.time()))

    # create calls
    if calls is None:
        calls = call_creation._create_calls(
            methods=methods,
            samples=samples,
            random_seed=random_seed,
            calls_file=calls_file,
        )

    # print prelude
    if verbose:
        latency_test_outputs._print_benchmark_prelude(
            nodes=nodes,
            methods=methods,
            samples=samples,
            random_seed=random_seed,
            calls=calls,
            output_file=output_file,
            start_time=start_time,
        )

    # perform calls
    latencies = latency_test_execution._execute_calls(
        nodes=nodes, calls=calls, verbose=verbose
    )

    # print summary
    if verbose:
        latency_test_outputs._print_benchmark_summary(
            latencies=latencies, calls=calls, start_time=start_time
        )

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

