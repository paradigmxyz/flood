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


def compute_raw_output_metrics(
    raw_output: typing.Mapping[str, pl.DataFrame],
    results: typing.Mapping[str, spec.LoadTestOutput],
) -> typing.Mapping[str, spec.LoadTestOutput]:
    import polars as pl

    metrics: typing.MutableMapping[str, spec.LoadTestOutput] = {}
    for node_name, node_results in results.items():
        node_metrics = []
        for i, (target_rate, target_duration) in enumerate(
            zip(node_results['target_rate'], node_results['target_duration'])
        ):
            sample_metrics = compute_raw_output_sample_metrics(
                df=raw_output[node_name].filter(pl.col('sample_index') == i),
                target_rate=target_rate,
                target_duration=target_duration,
            )
            sample_metrics['raw_output'] = None
            node_metrics.append(sample_metrics)
        metrics[node_name] = {
            metric: [sample_metrics[metric] for sample_metrics in node_metrics]  # type: ignore # noqa: E501
            for metric in node_results.keys()
        }
    return metrics


def compute_raw_output_sample_metrics(
    df: pl.DataFrame, target_rate: int, target_duration: int
) -> spec.LoadTestOutputDatum:
    import polars as pl
    actual_rate = (
        pl.count()
        / (pl.col('timestamp').max() - pl.col('timestamp').min())
        * 1e9
    )
    actual_rate = actual_rate.alias('actual_rate')
    successful = df.filter(pl.col('status_code') == 200)
    total_duration = (  # type: ignore
        df.select(pl.col('timestamp') + pl.col('latency')).max()
    ) - df['timestamp'].min()
    total_duration = total_duration.rows()[0][0]
    status_codes = {}
    for k, v in df['status_code'].value_counts().rows():
        status_codes[str(k)] = v
    errors = df.filter(~pl.col('error').is_null())['error'].unique().to_list()

    metrics_df = df.select(
        pl.lit(target_rate).alias('target_rate'),
        actual_rate,
        pl.lit(target_duration).alias('target_duration'),
        (pl.max('timestamp') - pl.min('timestamp')).alias('actual_duration')
        / 1e9,
        pl.count().alias('requests'),
        pl.lit(len(successful) / total_duration).alias('throughput') * 1e9,
        (len(successful) / pl.count()).alias('success'),
        pl.min('latency').alias('min') / 1e9,
        pl.mean('latency').alias('mean') / 1e9,
        pl.median('latency').alias('p50') / 1e9,
        pl.quantile('latency', 0.90).alias('p90') / 1e9,
        pl.quantile('latency', 0.95).alias('p95') / 1e9,
        pl.quantile('latency', 0.99).alias('p99') / 1e9,
        pl.max('latency').alias('max') / 1e9,
        pl.struct(**status_codes, eager=True).alias('status_codes'),
        pl.Series([errors]).alias('errors'),
        (pl.col('timestamp').min() / 1e3)
        .cast(pl.Datetime)
        .cast(str)
        .alias('first_request_timestamp'),
        (pl.col('timestamp').max() / 1e3)
        .cast(pl.Datetime)
        .cast(str)
        .alias('last_request_timestamp'),
        ((pl.col('timestamp') + pl.col('latency')) / 1e3)
        .max()
        .cast(pl.Datetime)
        .cast(str)
        .alias('last_response_timestamp'),
        (
            (pl.col('timestamp') + pl.col('latency')).max()
            - pl.max('timestamp')
        ).alias('final_wait_time')
        / 1e9,
    )

    return metrics_df.to_dicts()[0]  # type: ignore

