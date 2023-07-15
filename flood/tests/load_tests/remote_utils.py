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

    flood_version = flood.__version__

    # add git commit hash if not in a tagged release
    try:
        import os

        module_dir = flood.__path__[0]
        parent_dir = os.path.dirname(module_dir)
        parent_dir_files = os.listdir(parent_dir)
        if 'pyproject.toml' in parent_dir_files and '.git' in parent_dir_files:
            git_dir = os.path.join(parent_dir, '.git')

            # check whether in tagged release
            try:
                cmd = 'git --git-dir={git_dir} describe --tags --exact-match'
                cmd = cmd.format(git_dir=git_dir)
                subprocess.check_call(cmd.split(' '), stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                # get git commit
                cmd = 'git --git-dir={git_dir} rev-parse HEAD'.format(
                    git_dir=git_dir
                )
                output = subprocess.check_output(cmd.split(' '))
                git_commit = output.decode().strip()

                # specify commit in flood version
                flood_version = flood.__version__ + '-' + git_commit[:8]
    except Exception:
        pass

    return {
        'flood_version': flood_version,
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

