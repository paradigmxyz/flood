from __future__ import annotations

import typing

_slot_sample_path = '/tmp/flood/slot_samples.parquet'


def generate_slots(n: int) -> typing.Sequence[tuple[str, str]]:
    import polars as pl

    df = pl.read_parquet(_slot_sample_path)
    df = df[['contract_address', 'slot']]
    df = '0x' + df.select(pl.col('*').bin.encode('hex'))
    rows = df.sample(n).rows()
    return [(contract_address, slot) for contract_address, slot in rows]


def _create_slots_samples(
    samples_per_file: int = 100_000,
    output_path: str | None = None,
) -> None:
    import os
    import glob
    import polars as pl
    import pdp

    print('creating slots samples')

    source = pdp.get_dataset_glob('ethereum_slots')
    paths = glob.glob(source)
    samples = []
    for p, path in enumerate(paths):
        print(p + 1, '/', len(paths))
        samples.append(pl.read_parquet(path).sample(samples_per_file))

    if output_path is None:
        output_path = _slot_sample_path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = pl.concat(samples)
    df.write_parquet(output_path)
    print('output slot samples to', output_path)

