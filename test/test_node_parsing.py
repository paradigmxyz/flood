from __future__ import annotations

import pytest

import rpc_bench.benchmark


names = [None, 'test_node', 'backup_node']

valid_hosts = ['localhost', '61.4.1.34', '12.53.23.35', 'some_provider.com']

valid_ports = ['', ':8545', ':80']

url_prefixes = ['', 'http://', 'https://']

url_suffixes = ['/provider_key', '']

remote_clients = [None]
for host in valid_hosts:
    remote_clients.append(host)
    remote_clients.append('username@' + host)


@pytest.mark.parametrize('name', names)
@pytest.mark.parametrize('remote_client', remote_clients)
@pytest.mark.parametrize('url_prefix', url_prefixes)
@pytest.mark.parametrize('node_host', valid_hosts)
@pytest.mark.parametrize('port', valid_ports)
@pytest.mark.parametrize('url_suffix', url_suffixes)
def test_parse_node(
    name,
    remote_client,
    url_prefix,
    node_host,
    port,
    url_suffix,
):
    node_url = url_prefix + node_host + port + url_suffix
    node_str = node_url
    if remote_client is not None:
        node_str = remote_client + ':' + node_str
    unnamed_node_str = node_str
    if name is not None:
        node_str = name + '=' + node_str

    parsed = rpc_bench.benchmark._parse_node(node_str)

    if name is not None:
        assert parsed['name'] == name
    else:
        assert parsed['name'] == unnamed_node_str

    if url_prefix != '':
        assert parsed['url'] == node_url
    elif (
        node_url.startswith('localhost')
        or node_url.startswith('0.0.0.0')
        or node_url.startswith('127.0.0.1')
    ):
        assert parsed['url'] == 'http://' + node_url
    else:
        assert parsed['url'] == 'https://' + node_url

    assert parsed['remote'] == remote_client

