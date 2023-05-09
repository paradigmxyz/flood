from __future__ import annotations

import typing

if typing.TYPE_CHECKING:

    import polars as pl

    class RawVegetaTestOutput(typing.TypedDict):
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

    class VegetaTestOutput(typing.TypedDict):
        target_rate: int
        actual_rate: float
        requests: int
        throughput: float
        success: float
        min: float
        mean: float
        p50: float
        p90: float
        p95: float
        p99: float
        max: float

    class VegetaTestsOutput(typing.TypedDict):
        target_rate: typing.Sequence[int]
        actual_rate: typing.Sequence[float]
        requests: typing.Sequence[int]
        throughput: typing.Sequence[float]
        success: typing.Sequence[float]
        min: typing.Sequence[float]
        mean: typing.Sequence[float]
        p50: typing.Sequence[float]
        p90: typing.Sequence[float]
        p95: typing.Sequence[float]
        p99: typing.Sequence[float]
        max: typing.Sequence[float]


def run_loadtests(
    url: str,
    rates: typing.Sequence[int],
    calls: typing.Sequence[typing.Any],
    duration: int = 5,
    verbose: bool = True,
    output_format: typing.Literal['dict', 'polars'] = 'dict',
) -> VegetaTestsOutput | pl.DataFrame:

    # validate inputs
    if len(rates) == 0:
        raise Exception('must specify at least one rate')

    # perform tests
    reports = []
    for rate in rates:
        if verbose:
            print('running loadtest, rate =', rate)
        report = run_loadtest(
            calls=calls,
            url=url,
            duration=duration,
            rate=rate,
        )
        reports.append(report)

    # format output
    if output_format == 'dict':
        return {  # type: ignore
            key: [report[key] for report in reports]  # type: ignore
            for key in reports[0].keys()
        }

    elif output_format == 'polars':
        import polars as pl

        return pl.DataFrame(reports)

    else:
        raise Exception('invalid output_format: ' + str(output_format))


def run_loadtest(
    url: str,
    rate: int,
    calls: typing.Sequence[typing.Any],
    *,
    duration: int = 5,
) -> VegetaTestOutput:
    attack = _construct_vegeta_attack(
        calls=calls,
        url=url,
        verbose=False,
    )
    attack_output = _run_vegeta_attack(
        schedule_dir=attack['schedule_dir'],
        duration=duration,
        rate=rate,
    )
    report = _create_vegeta_report(
        attack_output=attack_output,
        target_rate=rate,
    )
    return report


def _construct_vegeta_attack(
    calls: typing.Sequence[typing.Any],
    url: str,
    schedule_dir: str | None = None,
    verbose: bool = True,
) -> typing.Mapping[str, str]:
    import json
    import os
    import tempfile

    headers = {"Content-Type": "application/json"}

    # determine output directory
    if schedule_dir is None:
        schedule_dir = tempfile.mkdtemp()

    # create calls file
    call_paths = []
    for c, call in enumerate(calls):
        vegeta_calls_path = os.path.join(
            schedule_dir, "vegeta_calls_" + str(c) + ".json"
        )
        with open(vegeta_calls_path, 'w') as f:
            f.write(json.dumps(call))
        call_paths.append(vegeta_calls_path)

    # create targets specification
    vegeta_targets_path = os.path.join(schedule_dir, "vegeta_targets")
    with open(vegeta_targets_path, "w") as f:
        for c, call in enumerate(calls):
            f.write("POST " + url + '\n')
            for key, value in headers.items():
                f.write(key + ": " + value + '\n')
            f.write("@" + call_paths[c] + '\n')
            f.write('\n')

    # output summary
    if verbose:
        print("created files:")
        print('- targets:', vegeta_targets_path)
        print('- calls:', vegeta_calls_path)
        print()
        print("run using:")
        print(
            "vegeta attack -targets "
            + vegeta_targets_path
            + ' -duration=5s | vegeta report'
        )

    return {
        'schedule_dir': schedule_dir,
        'vegeta_calls_path': vegeta_calls_path,
        'vegeta_targets_path': vegeta_targets_path,
    }


def _run_vegeta_attack(
    schedule_dir: str,
    *,
    duration: int | None = None,
    rate: int | None = None,
    max_connections: int | None = None,
    max_workers: int | None = None,
    n_cpus: int | None = None,
    report_path: str | None = None,
    cli_args: typing.Mapping[str, str | None] | None = None,
) -> bytes:
    import os
    import subprocess

    # construct command
    cmd = 'vegeta attack'
    cmd += ' -targets=' + os.path.join(schedule_dir, 'vegeta_targets')
    if duration is not None:
        cmd += ' -duration=' + str(duration)
    if rate is not None:
        cmd += ' -rate=' + str(rate)
    if duration is not None:
        cmd += ' -duration=' + str(duration)
    if max_connections is not None:
        cmd += ' -max-connections=' + str(max_connections)
    if max_workers is not None:
        cmd += ' -max-workers=' + str(max_workers)
    if cli_args is not None:
        for key, value in cli_args.items():
            cmd += '-' + key
            if value is not None:
                cmd += '=' + str(value)

    # run command
    return subprocess.check_output(cmd.split(' '))


def _create_vegeta_report(
    attack_output: bytes, target_rate: int
) -> VegetaTestOutput:
    import json
    import subprocess

    cmd = 'vegeta report -type json'
    report_output = (
        subprocess.check_output(cmd.split(' '), input=attack_output)
        .decode()
        .strip()
    )
    report: RawVegetaTestOutput = json.loads(report_output)
    return {
        'target_rate': target_rate,
        'actual_rate': report['rate'],
        'requests': report['requests'],
        'throughput': report['throughput'],
        'success': float(report['success']),
        'min': report['latencies']['min'] / 1e9,
        'mean': report['latencies']['mean'] / 1e9,
        'p50': report['latencies']['50th'] / 1e9,
        'p90': report['latencies']['90th'] / 1e9,
        'p95': report['latencies']['95th'] / 1e9,
        'p99': report['latencies']['99th'] / 1e9,
        'max': report['latencies']['max'] / 1e9,
    }

