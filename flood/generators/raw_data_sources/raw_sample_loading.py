from __future__ import annotations

import typing

import flood
from flood import generators
from . import raw_data_spec
from . import raw_download_utils

if typing.TYPE_CHECKING:
    import polars as pl


def get_raw_samples_path(
    network: str,
    datatype: str,
    *,
    size: str | None = None,
    version: str = raw_data_spec.raw_data_version,
    samples_dir: str | None = None,
) -> str | None:
    import os

    if samples_dir is None:
        samples_dir = generators.get_flood_samples_dir()

    # get largest_available file present
    if size is None:
        size = 'largest_available'
    if size == 'largest_available':
        import glob

        path_glob = raw_data_spec.raw_data_file_template.format(
            network=network,
            datatype=datatype,
            size='*',
            version=version,
        )
        filepaths = glob.glob(os.path.join(samples_dir, path_glob))
        if len(filepaths) > 0:
            sizes = [(os.stat(path).st_size, path) for path in filepaths]
            return max(sizes)[1]
        else:
            return None

    else:
        filename = raw_data_spec.raw_data_file_template.format(
            network=network,
            datatype=datatype,
            size=size,
            version=version,
        )
        return os.path.join(samples_dir, filename)


def load_raw_samples(
    network: str,
    datatype: str,
    *,
    size: str | None = None,
    version: str = raw_data_spec.raw_data_version,
    samples_dir: str | None = None,
    download_missing: str | None = 'L',
) -> pl.DataFrame:
    path = get_raw_samples_path(
        datatype=datatype,
        network=network,
        size=size,
        version=version,
        samples_dir=samples_dir,
    )
    if path is None:
        if download_missing is not None:
            if size is None:
                size = 'L'
            raw_download_utils.download_raw_data(
                network=network,
                datatypes=[datatype],
                version=version,
                output_dir=samples_dir,
                sizes=[download_missing],
            )
            path = get_raw_samples_path(
                datatype=datatype,
                network=network,
                size=size,
                version=version,
                samples_dir=samples_dir,
            )
            if path is None:
                raise Exception('could not download necessary data')
        else:
            raise Exception('no raw samples found to load')
    return pl.read_parquet(path)


def load_samples(
    network: str,
    datatype: str,
    n: int,
    *,
    size: str | None = None,
    version: str = raw_data_spec.raw_data_version,
    samples_dir: str | None = None,
    binary_convert: bool = True,
    download_missing: bool = True,
    random_seed: flood.RandomSeed | None = None,
) -> typing.Sequence[typing.Any]:
    import polars as pl

    # get path
    path = get_raw_samples_path(
        datatype=datatype,
        network=network,
        size=size,
        version=version,
        samples_dir=samples_dir,
    )
    if path is None:
        # download data if need be
        if download_missing:
            if size is None:
                size = 'L'
            raw_download_utils.download_raw_data(
                network=network,
                datatypes=[datatype],
                version=version,
                output_dir=samples_dir,
                sizes=[size],
            )
            path = get_raw_samples_path(
                datatype=datatype,
                network=network,
                size=size,
                version=version,
                samples_dir=samples_dir,
            )
            if path is None:
                raise Exception('could not download necessary data')
        else:
            raise Exception('no raw samples found to load')

    columns = {
        'contracts': ['contract_address'],
        'eoas': ['eoa'],
        'transactions': ['transaction_hash'],
        'slots': ['contract_address', 'slot'],
    }[datatype]

    df = pl.scan_parquet(path).select(columns).collect()
    if n > len(df):
        import math

        n_copies = math.ceil(n / len(df))
        df = pl.concat(n_copies * [df])
    if n < len(df):
        rng = generators.get_rng(random_seed=random_seed)
        seed = rng.integers(1_000_000_000, size=1)[0]
        df = df.sample(n, shuffle=True, seed=seed)

    for column in df.select(pl.col(pl.Binary)).columns:
        df = df.with_columns(
            ('0x' + pl.col(column).bin.encode('hex')).alias(column)
        )

    if len(columns) == 1:
        return df[columns[0]].to_list()
    else:
        return df.rows()
