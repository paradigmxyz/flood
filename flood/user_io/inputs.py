from __future__ import annotations

import typing

import flood
from flood import spec


def get_ctc_alias_url(url: str) -> str | None:
    try:
        import ctc.config

        ctc_providers = ctc.config.get_providers()
        if url in ctc_providers:
            url = ctc_providers[url]['url']
        return url
    except ImportError:
        return None


def get_nodes_network(nodes: typing.Mapping[str, spec.Node]) -> str:
    raise NotImplementedError()


#     request = {'jsonrpc': '2.0', 'method': 'eth_chainId', 'params': [], 'id': 1}

#     networks = []
#     for node in nodes.values():
#         chain_id = ctc.rpc.sync_eth_chain_id(context=provider)


def parse_nodes(
    nodes: spec.NodesShorthand,
    *,
    verbose: bool | int = False,
) -> typing.Mapping[str, spec.Node]:
    """parse given nodes according to input specification"""
    if verbose:
        flood.print_header('Gathering node data...')

    new_nodes: typing.MutableMapping[str, spec.Node] = {}
    if isinstance(nodes, list):
        import multiprocessing

        with multiprocessing.Pool() as pool:
            results = pool.map(parse_node, nodes)
        new_nodes = {result['name']: result for result in results}
    elif isinstance(nodes, dict):
        for key, value in nodes.items():
            new_nodes[key] = value
    else:
        raise Exception('invalid format for nodes')

    if verbose:
        print_nodes_table(new_nodes)

    return new_nodes


def print_nodes_table(nodes: typing.Mapping[str, spec.Node]) -> None:
    rows = []
    for node in nodes.values():
        url = node['url']
        if node['remote'] is not None:
            url += '\n' + node['remote']
        row = [
            node['name'],
            url,
            node['client_version'],
        ]
        rows.append(row)
    labels = ['node', 'url', 'version']
    print()
    flood.print_multiline_table(
        rows=rows,
        labels=labels,
        indent=4,
    )


def _get_node_str(node: flood.Node) -> str:
    node_str = '"' + node['name'] + '", url=' + node['url']
    remote = node['remote']
    if remote is not None:
        node_str += ' remote=' + remote
    if node['client_version'] is not None:
        node_str = node_str + ' version=' + node['client_version']
    return node_str


def parse_node(node: str | spec.Node) -> spec.Node:
    """parse node according to input specification"""
    prefixes = ['http', 'https', 'ws', 'wss']

    if isinstance(node, dict):
        return node
    elif isinstance(node, str):
        # parse name
        if '=' in node:
            name, url = node.split('=')
        else:
            name = node
            url = node

        # check if node is in ctc aliases
        alias_url = get_ctc_alias_url(url)
        if alias_url is not None:
            url = alias_url

        # parse remote and url
        if ':' in url:
            head, tail = url.split(':', 1)
            if head in prefixes:
                remote = None
                url = head + ':' + tail
            else:
                if tail.split('/')[0].isdecimal():
                    remote = None
                    url = url
                else:
                    remote = head
                    url = tail
        else:
            remote = None

        # add missing prefix
        if not any(url.startswith(prefix) for prefix in prefixes):
            # check if is ip
            pieces = url.split(':')[0].split('.')
            is_ip = len(pieces) == 4 and all(
                piece.isdecimal() for piece in pieces
            )

            # add prefix
            if url.startswith('localhost') or is_ip:
                url = 'http://' + url
            else:
                url = 'https://' + url

        client_version = get_node_client_version(url=url, remote=remote)

        return {
            'name': name,
            'url': url,
            'remote': remote,
            'client_version': client_version,
        }

    else:
        raise Exception('invalid node format')


def get_node_client_version(url: str, remote: str | None = None) -> str | None:
    try:
        if remote is None:
            import ctc.rpc

            info: str = ctc.rpc.sync_web3_client_version(
                context={'provider': url}
            )
            return info
        else:
            import json
            import subprocess

            cmd = [
                """ssh""",
                remote,
                """curl -X POST -H 'Content-Type: application/json' -d '{\"jsonrpc\": \"2.0\", \"method\": \"web3_clientVersion\", \"params\": [], \"id\": 1}' """
                + url,
            ]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            response = json.loads(output)
            info = response['result']
            return info
    except Exception:
        return None


def parse_test_data(test: spec.LoadTest) -> spec.LoadTestColumnWise:
    rates = []
    durations = []
    vegeta_kwargs = []
    calls = []
    for attack in test:
        rates.append(attack['rate'])
        durations.append(attack['duration'])
        vegeta_kwargs.append(attack['vegeta_kwargs'])
        calls.append(attack['calls'])
    return {
        'rates': rates,
        'durations': durations,
        'vegeta_kwargs': vegeta_kwargs,
        'calls': calls,
    }

