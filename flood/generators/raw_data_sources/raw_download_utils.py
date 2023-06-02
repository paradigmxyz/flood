from __future__ import annotations

from . import raw_data_spec


def download_samples(
    *,
    datatype: str,
    network: str,
    size: str,
    version: str | None = None,
    output_dir: str | None = None,
) -> None:
    import os
    import pdp

    if version is None:
        version = 'v1_0_0'
    if output_dir is None:
        output_dir = get_flood_samples_dir()

    filename = raw_data_spec.file_template.format(
        datatype=datatype,
        network=network,
        size=size,
        version=version,
    )
    output_path = os.path.join(output_dir, filename)
    url_root_template = (
        'https://datasets.paradigm.xyz/evm_samples/ethereum_samples__{version}/'
    )
    url_root = url_root_template.format(network=network, version=version)
    url = url_root + filename

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

