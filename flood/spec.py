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
        vegeta_args: VegetaArgs

    VegetaArgs = typing.Union[str, None]
    MultiVegetaArgs = typing.Sequence[VegetaArgs]
    VegetaArgsShorthand = typing.Union[VegetaArgs, MultiVegetaArgs]

    class TestGenerationParameters(typing.TypedDict):
        flood_version: str
        test_name: str
        random_seed: RandomSeed | None
        rates: typing.Sequence[int] | None
        durations: typing.Sequence[int] | None
        vegeta_args: VegetaArgsShorthand | None
        network: str

    # LoadTest = typing.Sequence[VegetaAttack]
    class LoadTest(typing.TypedDict):
        test_parameters: TestGenerationParameters
        attacks: typing.Sequence[VegetaAttack]

    class LoadTestColumnWise(typing.TypedDict):
        rates: typing.Sequence[int]
        durations: typing.Sequence[int]
        calls: typing.Sequence[typing.Sequence[typing.Any]]
        vegeta_args: typing.Sequence[typing.Any]

    LoadTestMode = typing.Literal['stress', 'spike', 'soak']

    LoadTestGenerator = typing.Callable[..., typing.Sequence[VegetaAttack]]
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
        actual_rate: float | None
        target_duration: int
        actual_duration: float | None
        requests: int
        throughput: float | None
        success: float | None
        min: float | None
        mean: float | None
        p50: float | None
        p90: float | None
        p95: float | None
        p99: float | None
        max: float | None
        status_codes: typing.Mapping[str, int]
        errors: typing.Sequence[str]
        first_request_timestamp: str | None
        last_request_timestamp: str | None
        last_response_timestamp: str | None
        final_wait_time: float | None
        # additional deep keys
        deep_raw_output: str | None
        deep_metrics: typing.Mapping[
            ResponseCategory, LoadTestDeepOutputDatum
        ] | None
        deep_rpc_error_pairs: typing.Sequence[ErrorPair] | None

    ResponseCategory = typing.Literal['all', 'successful', 'failed']
    ErrorPair = tuple[typing.Any, typing.Any]

    class LoadTestDeepOutputDatum(typing.TypedDict):
        target_rate: int
        actual_rate: float | None
        target_duration: int
        actual_duration: float | None
        requests: int
        throughput: float | None
        success: float | None
        min: float | None
        mean: float | None
        p50: float | None
        p90: float | None
        p95: float | None
        p99: float | None
        max: float | None
        status_codes: typing.Mapping[str, int]
        errors: typing.Sequence[str]
        first_request_timestamp: str | None
        last_request_timestamp: str | None
        last_response_timestamp: str | None
        final_wait_time: float | None
        # additional deep keys:
        n_invalid_json_errors: int
        n_rpc_errors: int

    class LoadTestOutput(typing.TypedDict):
        target_rate: typing.Sequence[int]
        actual_rate: typing.Sequence[float | None]
        target_duration: typing.Sequence[int]
        actual_duration: typing.Sequence[float | None]
        requests: typing.Sequence[int]
        throughput: typing.Sequence[float | None]
        success: typing.Sequence[float | None]
        min: typing.Sequence[float | None]
        mean: typing.Sequence[float | None]
        p50: typing.Sequence[float | None]
        p90: typing.Sequence[float | None]
        p95: typing.Sequence[float | None]
        p99: typing.Sequence[float | None]
        max: typing.Sequence[float | None]
        status_codes: typing.Sequence[typing.Mapping[str, int]]
        errors: typing.Sequence[typing.Sequence[str]]
        first_request_timestamp: typing.Sequence[str | None]
        last_request_timestamp: typing.Sequence[str | None]
        last_response_timestamp: typing.Sequence[str | None]
        final_wait_time: typing.Sequence[float | None]
        # additional deep keys
        deep_raw_output: typing.Sequence[str | None] | None
        deep_metrics: typing.Mapping[
            ResponseCategory, LoadTestDeepOutput
        ] | None
        deep_rpc_error_pairs: typing.Sequence[
            typing.Sequence[ErrorPair] | None
        ] | None

    class LoadTestDeepOutput(typing.TypedDict):
        target_rate: typing.Sequence[int]
        actual_rate: typing.Sequence[float | None]
        target_duration: typing.Sequence[int]
        actual_duration: typing.Sequence[float | None]
        requests: typing.Sequence[int]
        throughput: typing.Sequence[float | None]
        success: typing.Sequence[float | None]
        min: typing.Sequence[float | None]
        mean: typing.Sequence[float | None]
        p50: typing.Sequence[float | None]
        p90: typing.Sequence[float | None]
        p95: typing.Sequence[float | None]
        p99: typing.Sequence[float | None]
        max: typing.Sequence[float | None]
        status_codes: typing.Sequence[typing.Mapping[str, int]]
        errors: typing.Sequence[typing.Sequence[str]]
        first_request_timestamp: typing.Sequence[str | None]
        last_request_timestamp: typing.Sequence[str | None]
        last_response_timestamp: typing.Sequence[str | None]
        final_wait_time: typing.Sequence[float | None]
        # additional deep keys:
        n_invalid_json_errors: typing.Sequence[int]
        n_rpc_errors: typing.Sequence[int]

    RunType = typing.Literal['single_test']  # noqa: F821
    DeepOutput = typing.Literal['raw', 'metrics']

    class SingleRunTestPayload(typing.TypedDict):
        flood_version: str
        type: RunType
        name: str
        test_parameters: TestGenerationParameters

    class SingleRunResultsPayload(typing.TypedDict):
        flood_version: str
        dependency_versions: typing.Mapping[str, str | None]
        cli_args: typing.Sequence[str]
        type: RunType
        t_run_start: float
        t_run_end: float
        nodes: Nodes
        results: typing.Mapping[str, LoadTestOutput]

    # runner outputs

    class RunOutput(typing.TypedDict):
        single_run: SingleRunOutput

    class SingleRunOutput(typing.TypedDict):
        output_dir: str
        test: LoadTest | None
        test_parameters: TestGenerationParameters
        payload: SingleRunResultsPayload

    #
    # # env / ops management
    #

    class FloodInstallation(typing.TypedDict):
        vegeta_path: str | None
        flood_version: str | None
        git_dir: str | None
        git_commit: str | None
        semver: str | None


class SshError(Exception):
    pass

