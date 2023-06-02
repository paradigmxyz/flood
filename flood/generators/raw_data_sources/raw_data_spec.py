from __future__ import annotations


file_template = "{network}_{datatype}_samples__{size}__{version}.parquet"

default_sizes = {
    "XS": 1_000,
    "S": 10_000,
    "M": 100_000,
    "L": 1_000_000,
    "XL": 10_000_000,
}
