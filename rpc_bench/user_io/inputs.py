from __future__ import annotations

import typing

from rpc_bench import spec


def get_ctc_alias_url(url: str) -> str | None:
    try:
        import ctc.config

        ctc_providers = ctc.config.get_providers()
        if url in ctc_providers:
            url = ctc_providers[url]['url']
        return url
    except ImportError:
        return None


def parse_nodes(nodes: spec.NodesShorthand) -> typing.Mapping[str, spec.Node]:
    """parse given nodes according to input specification"""
    new_nodes: typing.MutableMapping[str, spec.Node] = {}
    if isinstance(nodes, list):
        for node in nodes:
            new_node = parse_node(node)
            new_nodes[new_node['name']] = new_node
    elif isinstance(nodes, dict):
        for key, value in nodes.items():
            new_nodes[key] = value
    else:
        raise Exception('invalid format for nodes')
    return new_nodes


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

        return {
            'name': name,
            'url': url,
            'remote': remote,
        }

    else:
        raise Exception('invalid node format')


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

