"""type definitions for typing annotations"""

from __future__ import annotations

import typing


if typing.TYPE_CHECKING:
    #
    # # generic types
    #

    Call = typing.Mapping[str, typing.Mapping[str, typing.Any]]

    MethodCalls = typing.Mapping[str, typing.Sequence[typing.Any]]

    class Node(typing.TypedDict):
        name: str
        url: str
        remote: str | None
        client_version: str | None
        network: str | int | None

    NodeShorthand = typing.Union[str, Node]

    NodesShorthand = typing.Union[
        typing.Sequence[str],
        typing.Sequence[Node],
        typing.Mapping[str, str],
        typing.Mapping[str, Node],
    ]
    Nodes = typing.Mapping[str, Node]

    class ProgressBar(typing.TypedDict):
        desc: str
        position: int | None
        leave: bool
        colour: str
        disable: bool

    #
    # # generators
    #

    import numpy as np

    RandomSeed = typing.Union[int, np.random._generator.Generator]

    #
    # # latency test types
    #

    NodeMethodLatencies = typing.Mapping[str, typing.Sequence[float]]
    NodesMethodLatencies = typing.Mapping[str, NodeMethodLatencies]

    class LatencyBenchmarkResults(typing.TypedDict):
        nodes: typing.Mapping[str, Node]
        methods: typing.Sequence[str]
        samples: int | None
        calls: typing.Mapping[str, typing.Sequence[str]]
        latencies: NodesMethodLatencies

    #
    # # equality test
    #

    EqualityTest = tuple[
        str,
        typing.Callable[..., typing.Any],
        typing.Sequence[typing.Any],
        typing.Mapping[str, typing.Any],
    ]

    #
    # # load test types
    #

    class VegetaAttack(typing.TypedDict):
        rate: int
        duration: int
        calls: typing.Sequence[typing.Any]
        vegeta_kwargs: typing.Mapping[str, typing.Any]

    VegetaKwargs = typing.Mapping[str, typing.Union[str, None]]
    MultiVegetaKwargs = typing.Sequence[VegetaKwargs]
    VegetaKwargsShorthand = typing.Union[VegetaKwargs, MultiVegetaKwargs]

    LoadTest = typing.Sequence[VegetaAttack]

    class LoadTestColumnWise(typing.TypedDict):
        rates: typing.Sequence[int]
        durations: typing.Sequence[int]
        calls: typing.Sequence[typing.Sequence[typing.Any]]
        vegeta_kwargs: typing.Sequence[typing.Any]

    LoadTestMode = typing.Literal['stress', 'spike', 'soak']

    LoadTestGenerator = typing.Callable[..., LoadTest]
    MultiLoadTestGenerator = typing.Callable[..., typing.Mapping[str, LoadTest]]

    #
    # # load tests outputs
    #

    class RawLoadTestOutputDatum(typing.TypedDict):
        latencies: typing.Mapping[str, float]
        bytes_in: typing.Mapping[str, int]
        bytes_out: typing.Mapping[str, int]
        earliest: str
        latest: str
        end: str
        duration: int
        wait: int
        requests: int
        rate: float
        throughput: float
        success: int
        status_codes: typing.Mapping[str, int]
        errors: typing.Sequence[str]
        first_request_timestamp: str
        last_request_timestamp: str
        last_response_timestamp: str
        final_wait_time: int

    class LoadTestOutputDatum(typing.TypedDict):
        target_rate: int
        actual_rate: float
        target_duration: int
        actual_duration: float
        requests: int
        throughput: float
        success: float
        min: float | None
        mean: float
        p50: float
        p90: float
        p95: float
        p99: float
        max: float
        status_codes: typing.Mapping[str, int]
        errors: typing.Sequence[str]
        first_request_timestamp: str
        last_request_timestamp: str
        last_response_timestamp: str
        final_wait_time: float
        raw_output: str | None

    class LoadTestOutput(typing.TypedDict):
        target_rate: typing.Sequence[int]
        actual_rate: typing.Sequence[float]
        target_duration: typing.Sequence[int]
        actual_duration: typing.Sequence[float]
        requests: typing.Sequence[int]
        throughput: typing.Sequence[float]
        success: typing.Sequence[float]
        min: typing.Sequence[float | None]
        mean: typing.Sequence[float]
        p50: typing.Sequence[float]
        p90: typing.Sequence[float]
        p95: typing.Sequence[float]
        p99: typing.Sequence[float]
        max: typing.Sequence[float]
        status_codes: typing.Sequence[typing.Mapping[str, int]]
        errors: typing.Sequence[typing.Sequence[str]]
        first_request_timestamp: typing.Sequence[str]
        last_request_timestamp: typing.Sequence[str]
        last_response_timestamp: typing.Sequence[str]
        final_wait_time: typing.Sequence[float]
        raw_output: typing.Sequence[str | None]

    RunType = typing.Literal['single_test']

    class SingleRunTestPayload(typing.TypedDict):
        version: str
        type: RunType
        name: str
        test: LoadTest

    class SingleRunResultsPayload(typing.TypedDict):
        version: str
        type: RunType
        nodes: Nodes
        results: typing.Mapping[str, LoadTestOutput]
