"""wrapper around the vegeta load testing tool"""
from __future__ import annotations

import typing

from .. import spec


def run_vegeta_attack(
    *,
    url: str,
    rate: int,
    calls: typing.Sequence[typing.Any],
    duration: int,
) -> spec.LoadTestOutputDatum:
    attack = _construct_vegeta_attack(
        calls=calls,
        url=url,
        verbose=False,
    )
    attack_output = _vegeta_attack(
        schedule_dir=attack['schedule_dir'],
        duration=duration,
        rate=rate,
    )
    report = _create_vegeta_report(
        attack_output=attack_output,
        target_rate=rate,
        target_duration=duration,
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

    headers = {'Content-Type': 'application/json'}

    # determine output directory
    if schedule_dir is None:
        schedule_dir = tempfile.mkdtemp()

    # create calls file
    call_paths = []
    for c, call in enumerate(calls):
        vegeta_calls_path = os.path.join(
            schedule_dir, 'vegeta_calls_' + str(c) + '.json'
        )
        with open(vegeta_calls_path, 'w') as f:
            f.write(json.dumps(call))
        call_paths.append(vegeta_calls_path)

    # create targets specification
    vegeta_targets_path = os.path.join(schedule_dir, 'vegeta_targets')
    with open(vegeta_targets_path, 'w') as f:
        for c, call in enumerate(calls):
            f.write('POST ' + url + '\n')
            for key, value in headers.items():
                f.write(key + ': ' + value + '\n')
            f.write('@' + call_paths[c] + '\n')
            f.write('\n')

    # output summary
    if verbose:
        print('created files:')
        print('- targets:', vegeta_targets_path)
        print('- calls:', vegeta_calls_path)
        print()
        print('run using:')
        print(
            'vegeta attack -targets '
            + vegeta_targets_path
            + ' -duration=5s | vegeta report'
        )

    return {
        'schedule_dir': schedule_dir,
        'vegeta_calls_path': vegeta_calls_path,
        'vegeta_targets_path': vegeta_targets_path,
    }


def _vegeta_attack(
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
    if rate is not None:
        cmd += ' -rate=' + str(rate)
    if duration is not None:
        cmd += ' -duration=' + str(duration) + 's'
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
    attack_output: bytes,
    target_rate: int,
    target_duration: int,
) -> spec.LoadTestOutputDatum:
    import json
    import subprocess

    cmd = 'vegeta report -type json'
    report_output = (
        subprocess.check_output(cmd.split(' '), input=attack_output)
        .decode()
        .strip()
    )
    report: spec.RawLoadTestOutputDatum = json.loads(report_output)
    return {
        'target_rate': target_rate,
        'actual_rate': report['rate'] / 1e9,
        'target_duration': target_duration,
        'actual_duration': report['duration'] / 1e9,
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

