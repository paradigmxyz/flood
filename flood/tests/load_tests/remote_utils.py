from __future__ import annotations

import subprocess
import typing

import flood


class SshError(Exception):
    pass


class FloodInstallation(typing.TypedDict):
    vegeta_path: str | None
    flood_version: str | None


def get_local_installation() -> FloodInstallation:
    result = subprocess.check_output(['which', 'vegeta'])
    vegeta_path = result.decode().rstrip()

    return {
        'flood_version': flood.__version__,
        'vegeta_path': vegeta_path,
    }


def get_remote_installation(
    host: str, username: str | None = None
) -> FloodInstallation:
    # create command
    if username is not None:
        url = username + '@' + host
    else:
        url = host
    template = (
        "ssh {url} bash -c "
        "'source ~/.profile; "
        "echo $(which vegeta); "
        "echo $(python3 -m flood version)'"
    )
    cmd = template.format(url=url)

    # run command
    try:
        result = subprocess.check_output(
            cmd.split(' '), stderr=subprocess.DEVNULL
        )
    except Exception:
        raise SshError('could not ssh')

    vegeta_path: str | None
    flood_version: str | None

    vegeta_path, flood_version = result.decode()[:-1].split('\n')
    if vegeta_path == '':
        vegeta_path = None
    if flood_version == '':
        flood_version = None
    return {'vegeta_path': vegeta_path, 'flood_version': flood_version}

