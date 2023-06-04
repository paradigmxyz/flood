from __future__ import annotations

import typing

from . import raw_data_spec


def download_raw_data(
    *,
    network: str,
    sizes: str | typing.Sequence[str],
    datatypes: typing.Sequence[str] | str | None = None,
    version: str | None = None,
    output_dir: str | None = None,
    only_missing: bool = False,
    verbose: bool = True,
) -> None:
    import os
    import pdp

    # process inputs
    if version is None:
        version = 'v1_0_0'
    if output_dir is None:
        output_dir = get_flood_samples_dir()
    if datatypes is None:
        datatypes = raw_data_spec.default_datatypes
    if isinstance(datatypes, str):
        datatypes = [datatypes]
    if isinstance(sizes, str):
        sizes = [sizes]
    elif isinstance(sizes, list):
        pass
    elif isinstance(sizes, dict):
        sizes = list(sizes.keys())
    else:
        raise Exception()
    url_root = raw_data_spec.raw_data_url_template.format(
        network=network, version=version
    )

    # download each datatype
    for datatype in datatypes:
        for size in sizes:
            filename = raw_data_spec.raw_data_file_template.format(
                datatype=datatype,
                network=network,
                size=size,
                version=version,
            )
            output_path = os.path.join(output_dir, filename)
            url = url_root + filename

            if only_missing and os.path.isfile(output_path):
                continue

            print('downloading', filename)
            pdp.download_file(url=url, output_path=output_path)


def get_flood_samples_dir() -> str:
    import os

    flood_samples_dir = os.environ.get('FLOOD_SAMPLES_DIR')
    if flood_samples_dir is None:
        import warnings

        warnings.warn('FLOOD_SAMPLES_DIR not set in env, defaulting to CWD')
        return os.path.join(os.getcwd(), 'flood_samples')
    else:
        return flood_samples_dir
