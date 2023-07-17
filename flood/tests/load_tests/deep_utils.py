from __future__ import annotations

import typing
from ... import spec

if typing.TYPE_CHECKING:
    import polars as pl


def compute_deep_datum(
    raw_output: bytes,
    target_rate: int,
    target_duration: int,
    calls: typing.Sequence[typing.Any],
) -> tuple[
    typing.Mapping[spec.ResponseCategory, spec.LoadTestDeepOutputDatum],
    typing.Sequence[spec.ErrorPair],
]:
    import polars as pl

    # convert to dataframe
    all_df = _convert_raw_vegeta_output_to_dataframe(raw_output)

    # add error columns
    rpc_error = []
    invalid_json_error = []
    for status_code, response in zip(all_df['status_code'], all_df['response']):
        if status_code == 200:
            try:
                import json
                import base64

                decoded = json.loads(base64.b64decode(response))

                invalid_json_error.append(False)
                if decoded.get('result') is None:
                    rpc_error.append(True)
                else:
                    rpc_error.append(False)

            except Exception:
                invalid_json_error.append(True)
                rpc_error.append(False)
        else:
            invalid_json_error.append(False)
            rpc_error.append(False)
    all_df = all_df.with_columns(
        pl.Series('invalid_json_error', invalid_json_error),
        pl.Series('rpc_error', rpc_error),
    )
    all_df = all_df.with_columns(
        (
            (pl.col('status_code') == 200)
            & ~pl.col('invalid_json_error')
            & ~pl.col('rpc_error')
        ).alias('deep_success')
    )

    # get error pairs
    rpc_error_pairs: typing.Sequence[spec.ErrorPair] = []
    rpc_error_pairs = _gather_error_pairs(df=all_df, calls=calls)

    # compute sample metrics
    category_data = {}
    dataframes: list[tuple[spec.ResponseCategory, pl.DataFrame]] = [
        ('all', all_df),
        ('successful', all_df.filter(pl.col('deep_success'))),
        ('failed', all_df.filter(~pl.col('deep_success'))),
    ]
    for category, df in dataframes:
        category_data[category] = _compute_raw_output_sample_metrics(
            df=df, target_rate=target_rate, target_duration=target_duration
        )

    return category_data, rpc_error_pairs


def _convert_raw_vegeta_output_to_dataframe(raw_output: bytes) -> pl.DataFrame:
    """convert raw vegeta attack output to dataframe, 1 row per response"""
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


def _gather_error_pairs(
    df: pl.DataFrame, calls: typing.Sequence[typing.Any]
) -> typing.Sequence[spec.ErrorPair]:
    import polars as pl

    calls_by_id = {}
    for call in calls:
        call_id = call.get('id')
        if call_id is None:
            raise Exception('id not specified for call')
        elif call_id in calls_by_id:
            raise Exception('duplicate call for id')
        calls_by_id[call_id] = call

    responses = df.filter(pl.col('rpc_error'))['response']

    pairs = []
    for response in responses:
        pairs.append((None, response))

    return pairs


def _compute_raw_output_sample_metrics(
    df: pl.DataFrame, target_rate: int, target_duration: int
) -> spec.LoadTestDeepOutputDatum:
    """convert standard test metrics from vegeta raw output dataframe"""
    if len(df) == 0:
        return {
            'target_rate': target_rate,
            'actual_rate': 0,
            'target_duration': target_duration,
            'actual_duration': None,
            'requests': 0,
            'throughput': None,
            'success': None,
            'min': None,
            'mean': None,
            'p50': None,
            'p90': None,
            'p95': None,
            'p99': None,
            'max': None,
            'status_codes': {},
            'errors': [],
            'first_request_timestamp': None,
            'last_request_timestamp': None,
            'last_response_timestamp': None,
            'final_wait_time': None,
            'n_invalid_json_errors': 0,
            'n_rpc_errors': 0,
        }

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

    output: spec.LoadTestDeepOutputDatum = metrics_df.to_dicts()[0]  # type: ignore # noqa: E501
    output['n_invalid_json_errors'] = int(df['invalid_json_error'].sum())
    output['n_rpc_errors'] = int(df['rpc_error'].sum())

    return output


# def compute_raw_output_metrics(
#     raw_output: typing.Mapping[str, pl.DataFrame],
#     results: typing.Mapping[str, spec.LoadTestOutput],
# ) -> typing.Mapping[str, spec.LoadTestOutput]:
#     import polars as pl

#     metrics: typing.MutableMapping[str, spec.LoadTestOutput] = {}
#     for node_name, node_results in results.items():
#         node_metrics = []
#         for i, (target_rate, target_duration) in enumerate(
#             zip(node_results['target_rate'], node_results['target_duration'])
#         ):
#             sample_metrics = compute_raw_output_sample_metrics(
#                 df=raw_output[node_name].filter(pl.col('sample_index') == i),
#                 target_rate=target_rate,
#                 target_duration=target_duration,
#             )
#             node_metrics.append(sample_metrics)
#         metrics[node_name] = {
#             metric: [sample_metrics[metric] for sample_metrics in node_metrics]  # type: ignore # noqa: E501
#             for metric in node_results.keys()
#         }
#     return metrics


# def test_run_to_deep_raw_vegeta_output(
#     results: typing.Mapping[str, spec.LoadTestOutput],
#     sample_index: int | typing.Sequence[int] | None = None,
# ) -> typing.Mapping[str, pl.DataFrame]:
#     import polars as pl

#     node_dfs = {}
#     for node_name, node_results in results.items():
#         raw_output = node_results['deep_raw_output']
#         if raw_output is None:
#             raise Exception('raw_outputs were not saved for test')
#         else:
#             if sample_index is not None:
#                 if isinstance(sample_index, int):
#                     indices = [sample_index]
#                 elif isinstance(sample_index, list):
#                     indices = sample_index
#                 else:
#                     raise Exception('invalid format for sample_index')
#             else:
#                 indices = list(range(len(raw_output)))
#             dfs = []
#             for index in indices:
#                 item = raw_output[index]
#                 if item is None:
#                     raise Exception('raw_outputs were not saved for test')
#                 decoded = decode_raw_vegeta_output(item)
#                 df = convert_raw_vegeta_output_to_dataframe(decoded)
#                 df = df.with_columns(pl.lit(index).alias('sample_index'))
#                 dfs.append(df)
#             node_dfs[node_name] = pl.concat(dfs)
#     return node_dfs


#
# # serde
#


def encode_raw_vegeta_output(raw_output: bytes) -> str:
    """encode raw output to str for use in JSON"""
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
    """decode raw output from str for use in JSON"""
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

