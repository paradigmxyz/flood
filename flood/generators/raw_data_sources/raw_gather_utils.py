from __future__ import annotations

import typing

from . import raw_data_spec

if typing.TYPE_CHECKING:
    import polars as pl


def create_samples_dataset(
    *,
    output_dir: str,
    network: str,
    version: str,
    sizes: typing.Mapping[str, int] | None = None,
    verbose: bool = True,
) -> None:
    # parse inputs
    if sizes is None:
        sizes = raw_data_spec.default_sizes
    max_size = max(sizes.values())

    # create samples
    if verbose:
        print('creating samples...')
    samples = create_raw_samples(n=max_size, network="ethereum")

    # write sample files
    if verbose:
        print('writing samples to disk...')
    write_raw_samples(
        samples=samples,
        output_dir=output_dir,
        sizes=sizes,
        network=network,
        version=version,
    )

    if verbose:
        print('sample dataset completed')


def create_raw_samples(
    n: int, network: str
) -> typing.Mapping[str, pl.DataFrame]:
    import glob
    import pdp
    from pdp.datasets import contracts
    import polars as pl

    # contracts
    contracts_df = contracts.query_contracts(
        columns=["contract_address", "block_number", "deployer"],
        network=network,
    ).sort("block_number")
    contracts_sample = contracts_df[
        ["contract_address", "block_number"]
    ].sample(n=n)

    # slots
    slot_glob = pdp.get_dataset_glob(
        network=network,
        datatype="slots",
    )
    pieces = []
    for file in glob.glob(slot_glob):
        piece = (
            pl.scan_parquet(file)
            .select("contract_address", "slot", "first_updated_block")
            .collect()
            .sample(int(n / 10))
        )
        pieces.append(piece)
    slots_sample = pl.concat(pieces).sample(n)
    slots_sample = slots_sample.rename(
        {
            "first_updated_block": "block_number",
        }
    )

    # slots
    native_transfers_glob = pdp.get_dataset_glob(
        network=network,
        datatype="native_transfers",
    )
    pieces = []
    for file in glob.glob(native_transfers_glob):
        piece = (
            pl.scan_parquet(file)
            .select("transaction_hash", "block_number")
            .collect()
        )
        if len(piece) > n / 50:
            piece = piece.sample(int(n / 50))
        pieces.append(piece)
    transactions_sample = pl.concat(pieces)

    # eoas
    native_transfers_glob = pdp.get_dataset_glob(
        network=network,
        datatype="native_transfers",
    )
    pieces = []
    for file in glob.glob(native_transfers_glob):
        piece = (
            pl.scan_parquet(file)
            .select("from_address", "block_number")
            .unique('from_address', keep='first')
            .collect()
        )
        if len(piece) > n / 50:
            piece = piece.sample(int(n / 50))
        pieces.append(piece)
    eoas_df = (
        pl.concat(pieces)
        .filter(~pl.col("from_address").is_in(contracts_df["contract_address"]))
        .unique("from_address")
        .rename({"from_address": "eoa"})
    )
    eoas_sample = eoas_df.sample(n)

    return {
        "contracts": contracts_sample,
        "eoas": eoas_sample,
        "slots": slots_sample,
        "transaction": transactions_sample,
    }


def write_raw_samples(
    samples: typing.Mapping[str, pl.DataFrame],
    *,
    output_dir: str,
    network: str,
    version: str,
    sizes: typing.Mapping[str, int] | None = None,
) -> None:
    import os

    path_template = os.path.join(output_dir, raw_data_spec.file_template)
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
                raise Exception("desired size is too big for sample data")

            # write file
            sized_data.write_parquet(output_path)

