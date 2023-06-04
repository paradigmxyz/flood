from __future__ import annotations

import typing

from . import raw_data_spec

if typing.TYPE_CHECKING:
    import polars as pl


def create_samples_dataset(
    *,
    output_dir: str,
    network: str,
    version: str | None = None,
    sizes: typing.Mapping[str, int] | typing.Sequence[str] | None = None,
    datatypes: typing.Sequence[str] | None = None,
    verbose: bool = True,
) -> None:
    # parse inputs
    if version is None:
        version = 'v1_0_0'
    if isinstance(sizes, list):
        sizes = {
            k: v for k, v in raw_data_spec.default_sizes.items() if k in sizes
        }
    elif isinstance(sizes, dict):
        pass
    elif sizes is None:
        sizes = raw_data_spec.default_sizes
    else:
        raise Exception('invalid sizes format: ' + str(type(sizes)))
    if datatypes is None:
        datatypes = raw_data_spec.default_datatypes
    max_size = max(sizes.values())

    # print summary
    if verbose:
        print('creating dataset of raw EVM samples')
        print('- version:', version)
        print('- datatypes:', datatypes)
        print('- network:', network)
        print('- sizes:', sizes)
        if output_dir is not None:
            print('- saving to:', output_dir)
        print()
        print('collecting samples...')

    # collect samples
    samples = _create_raw_samples(
        n=max_size,
        network='ethereum',
        datatypes=datatypes,
    )

    # write sample files
    if verbose:
        print('writing samples to disk...')
    _write_raw_samples(
        samples=samples,
        output_dir=output_dir,
        sizes=sizes,
        network=network,
        version=version,
    )

    if verbose:
        print('sample dataset completed')


def _create_raw_samples(
    n: int,
    network: str,
    datatypes: typing.Sequence[str] | None = None,
) -> typing.Mapping[str, pl.DataFrame]:
    import glob
    import pdp
    from pdp.datasets import contracts
    import polars as pl

    if datatypes is None:
        datatypes = raw_data_spec.default_datatypes

    samples = {}

    # contracts
    if 'contracts' in datatypes:
        contracts_df = contracts.query_contracts(
            columns=['contract_address', 'block_number', 'deployer'],
            network=network,
        ).sort('block_number')
        samples['contracts'] = contracts_df[
            ['contract_address', 'block_number']
        ].sample(n=n)

    # slots
    if 'slots' in datatypes:
        slot_glob = pdp.get_dataset_glob(
            network=network,
            datatype='slots',
        )
        pieces = []
        for file in glob.glob(slot_glob):
            piece = (
                pl.scan_parquet(file)
                .select('contract_address', 'slot', 'first_updated_block')
                .collect()
                .sample(int(n / 10))
            )
            pieces.append(piece)
        samples['slots'] = (
            pl.concat(pieces)
            .rename({'first_updated_block': 'block_number'})
            .sample(n)
        )

    # transactions
    if 'transactions' in datatypes:
        native_transfers_glob = pdp.get_dataset_glob(
            network=network,
            datatype='native_transfers',
        )
        pieces = []
        for file in glob.glob(native_transfers_glob):
            piece = (
                pl.scan_parquet(file)
                .select('transaction_hash', 'block_number')
                .collect()
            )
            if len(piece) > n / 50:
                piece = piece.sample(int(n / 50))
            pieces.append(piece)
        samples['transactions'] = pl.concat(pieces).sample(n)

    # eoas
    if 'eoas' in datatypes:
        native_transfers_glob = pdp.get_dataset_glob(
            network=network,
            datatype='native_transfers',
        )
        pieces = []
        for file in glob.glob(native_transfers_glob):
            piece = (
                pl.scan_parquet(file)
                .select('from_address', 'block_number')
                .unique('from_address', keep='first')
                .collect()
            )
            if len(piece) > n / 50:
                piece = piece.sample(int(n / 50))
            pieces.append(piece)
        eoas_df = (
            pl.concat(pieces)
            .filter(
                ~pl.col('from_address').is_in(contracts_df['contract_address'])
            )
            .unique('from_address')
            .rename({'from_address': 'eoa'})
        )
        samples['eoas'] = eoas_df.sample(n)

    return samples


def _write_raw_samples(
    samples: typing.Mapping[str, pl.DataFrame],
    *,
    output_dir: str,
    network: str,
    version: str,
    sizes: typing.Mapping[str, int] | None = None,
) -> None:
    import os

    path_template = os.path.join(
        output_dir, raw_data_spec.raw_data_file_template
    )
    if sizes is None:
        sizes = raw_data_spec.default_sizes

    for sample_name, sample_data in samples.items():
        for size_name, size in sizes.items():
            # get output path
            output_path = path_template.format(
                network=network,
                datatype=sample_name,
                size=size_name,
                version=version,
            )
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # shrink sample to size
            if len(sample_data) == size:
                sized_data = sample_data
            elif len(sample_data) > size:
                sized_data = sample_data[:size]
            else:
                raise Exception('desired size is too big for sample data')

            # write file
            sized_data.write_parquet(output_path)
