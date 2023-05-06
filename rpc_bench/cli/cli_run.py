from __future__ import annotations

import argparse
import typing

from rpc_bench import benchmark


def run_cli() -> None:
    args = parse_args()
    benchmark.run_latency_benchmark(
        nodes=args['nodes'],
        methods=args['methods'],
        samples=args['samples'],
        random_seed=args['random_seed'],
        output_file=args['output_file'],
    )


def parse_args() -> typing.Mapping[str, typing.Any]:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'nodes',
        nargs='+',
        help='nodes to test',
    )
    parser.add_argument(
        '--methods',
        nargs='+',
        help='RPC methods to test',
    )
    parser.add_argument(
        '-n',
        '--n-samples',
        type=int,
        dest='samples',
        default=1,
        help='number of times to call each method',
    )
    parser.add_argument(
        '--seed',
        dest='random_seed',
        help='random seed to use for call parameters',
    )
    parser.add_argument(
        '--output',
        dest='output_file',
        help='output JSON file where to save results',
    )
    args = parser.parse_args()

    return {
        'nodes': args.nodes,
        'methods': args.methods,
        'samples': args.samples,
        'random_seed': args.random_seed,
        'output_file': args.output_file,
    }

