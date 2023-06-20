"""wrapper around the vegeta load testing tool"""
from __future__ import annotations

import typing

from ... import spec

if typing.TYPE_CHECKING:
    import polars as pl


def run_vegeta_attack(
    *,
    url: str,
    rate: int,
    calls: typing.Sequence[typing.Any],
    duration: int,
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    verbose: bool = False,
    include_raw_output: bool = False,
) -> spec.LoadTestOutputDatum:
    attack = _construct_vegeta_attack(
        calls=calls,
        url=url,
        verbose=verbose,
    )
    attack_output = _vegeta_attack(
        schedule_dir=attack['schedule_dir'],
        duration=duration,
        rate=rate,
        vegeta_kwargs=vegeta_kwargs,
        verbose=verbose,
    )
    report = _create_vegeta_report(
        attack_output=attack_output,
        target_rate=rate,
        target_duration=duration,
        include_raw_output=include_raw_output,
    )
    return report


def _construct_vegeta_attack(
    calls: typing.Sequence[typing.Any],
    url: str,
    schedule_dir: str | None = None,
    verbose: bool = False,
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
        print('running vegeta attack...')
        print('- targets:', vegeta_targets_path)
        print('- calls:', vegeta_calls_path)

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
    vegeta_kwargs: typing.Mapping[str, str | None] | None = None,
    verbose: bool = False,
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
    if vegeta_kwargs is not None:
        for key, value in vegeta_kwargs.items():
            cmd += ' -' + key
            if value is not None:
                cmd += '=' + str(value)

    if verbose:
        print('- command:', cmd)

    # run command
    return subprocess.check_output(cmd.split(' '))


def _create_vegeta_report(
    attack_output: bytes,
    target_rate: int,
    target_duration: int,
    include_raw_output: bool,
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

    if 'min' in report['latencies']:
        latency_min = report['latencies']['min'] / 1e9
    else:
        latency_min = None

    if include_raw_output:
        raw_output = encode_raw_vegeta_output(attack_output)
    else:
        raw_output = None

    return {
        'target_rate': target_rate,
        'actual_rate': report['rate'],
        'target_duration': target_duration,
        'actual_duration': report['duration'] / 1e9,
        'requests': report['requests'],
        'throughput': report['throughput'],
        'success': float(report['success']),
        'min': latency_min,
        'mean': report['latencies']['mean'] / 1e9,
        'p50': report['latencies']['50th'] / 1e9,
        'p90': report['latencies']['90th'] / 1e9,
        'p95': report['latencies']['95th'] / 1e9,
        'p99': report['latencies']['99th'] / 1e9,
        'max': report['latencies']['max'] / 1e9,
        #
        'status_codes': report['status_codes'],
        'errors': report['errors'],
        'first_request_timestamp': report['earliest'],
        'last_request_timestamp': report['latest'],
        'last_response_timestamp': report['end'],
        'final_wait_time': report['wait'] / 1e9,
        'raw_output': raw_output,
    }


#
# # output processing
#


def encode_raw_vegeta_output(raw_output: bytes) -> str:
    import base64
    import io
    import gzip

    # gzip compress
    buf = io.BytesIO()
    f = gzip.GzipFile(fileobj=buf, mode='wb')
    f.write(raw_output)
    f.close()
    compressed = buf.getvalue()

    # encode as base64
    as_base64 = base64.b64encode(compressed).decode('utf-8')

    return as_base64


def decode_raw_vegeta_output(encoded_output: str) -> bytes:
    import base64
    import io
    import gzip

    # decode from base64
    as_bytes = base64.b64decode(encoded_output.encode())

    # gzip decompress
    buf = io.BytesIO(as_bytes)
    f = gzip.GzipFile(fileobj=buf, mode='rb')
    decompressed = f.read()
    f.close()

    return decompressed


def convert_raw_vegeta_output_to_dataframe(raw_output: bytes) -> pl.DataFrame:
    import io
    import subprocess
    import polars as pl

    cmd = 'vegeta encode --to csv'
    report_output = (
        subprocess.check_output(cmd.split(' '), input=raw_output)
        .decode()
        .strip()
    )

    buf = io.StringIO()
    buf.write(report_output)
    buf.seek(0)

    schema = [
        'timestamp',
        'status_code',
        'latency',
        'bytes_out',
        'bytes_in',
        'error',
        'response',
        'name',
        'index',
        'method',
        'url',
        'response_headers',
    ]
    dtypes = {
        'bytes_in': pl.Int64,
        'bytes_out': pl.Int64,
        'error': pl.Utf8,
        'index': pl.Int64,
        'latency': pl.Int64,
        'method': pl.Utf8,
        'name': pl.Utf8,
        'response': pl.Utf8,
        'response_headers': pl.Utf8,
        'status_code': pl.Int64,
        'timestamp': pl.Int64,
        'url': pl.Utf8,
    }
    return pl.read_csv(buf, new_columns=schema, has_header=False, dtypes=dtypes)

