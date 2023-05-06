from __future__ import annotations

import json
import os
import subprocess
import uuid

from . import spec


def benchmark_remote(remote_node: str, calls: spec.MethodCalls) -> spec.LatencyBenchmarkResults:
    """run rpc_bench on remote node specified as `user@remote:node_url`"""

    # parse node specification
    if ':' not in remote_node:
        raise Exception('node specification must include : character')
    ssh, node_url = remote_node.split(':')

    # save call data, saving methods to preserve ordering in json
    job_id = str(uuid.uuid4())
    tempdir = '/tmp/rpc_bench__' + job_id
    os.makedirs(tempdir)
    calls_path = os.path.join(tempdir, 'calls.json')
    calls_data = {'methods': list(calls.keys()), 'calls': calls}
    with open(calls_path, 'w') as f:
        json.dump(calls_data, f)

    # send call data to remote server
    cmd = 'rsync ' + calls_path + ' ' + ssh + ':' + calls_path
    subprocess.call(cmd.split(' '))

    # initiate benchmarks
    results_path = os.path.join(tempdir, 'results.json')
    cmd = 'ssh {host} rpc_bench --calls {calls_path} --output {output}'.format(
        host=ssh,
        calls_path=calls_path,
        output=results_path,
    )
    subprocess.check_output(cmd)

    # retrieve benchmark results
    cmd = 'rsync ' + ssh + ':' + results_path + ' ' + results_path
    subprocess.call(cmd.split(' '))

    # return results
    with open(results_path, 'r') as f:
        results: spec.LatencyBenchmarkResults = json.load(f)
        return results

