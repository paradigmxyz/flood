from __future__ import annotations


raw_data_version = 'v1_0_0'

raw_data_url_template = (
    'https://datasets.paradigm.xyz/evm_samples/{network}_samples__{version}/'
)
raw_data_file_template = (
    '{network}_{datatype}_samples__{size}__{version}.parquet'
)

default_sizes = {
    'XS': 1_000,
    'S': 10_000,
    'M': 100_000,
    'L': 1_000_000,
    'XL': 10_000_000,
}

default_datatypes = [
    'contracts',
    'eoas',
    'transactions',
    'slots',
]
