from __future__ import annotations

import typing

import rpc_bench
from . import equality_test_sets


def run_equality_test(
    test_name: str,
    nodes: rpc_bench.NodesShorthand,
    *,
    verbose: bool | int = True,
    random_seed: rpc_bench.RandomSeed | None = None,
) -> None:
    import json
    import requests
    import toolstr

    nodes = rpc_bench.parse_nodes(nodes)
    for node in nodes.values():
        if node['remote'] is not None:
            raise Exception('remote not supported for equality test')
    if len(nodes) != 2:
        raise Exception('should use two nodes in equality test')

    # get tests
    if test_name != 'all':
        raise NotImplementedError('must use test_name="all" for equality test')
    equality_tests = equality_test_sets.get_all_equality_tests()

    # print preamble
    rpc_bench.print_text_box('Running equality test')
    rpc_bench.print_bullet(key='nodes', value='')
    for n, node in enumerate(nodes.values()):
        toolstr.print(
            toolstr.add_style(str(n + 1), rpc_bench.styles['metavar'])
            + '. '
            + str(node),
            indent=4,
            style=rpc_bench.styles['description'],
        )
    rpc_bench.print_bullet(key='methods', value='')
    for test in equality_tests:
        rpc_bench.print_bullet(key=test[0], value='', colon_str='', indent=4)

    successful = []
    headers = {'Content-Type': 'application/json', 'User-Agent': 'rpc_bench'}
    for test in equality_tests:
        # create call
        test_name, constructor, args, kwargs = test
        call = constructor(*args, **kwargs)

        # dispatch call
        results = []
        for node in nodes.values():
            try:
                response = requests.post(
                    url=node['url'], data=json.dumps(call), headers=headers
                )
                response_data = response.json()
                if 'result' in response_data:
                    result = response_data['result']
                else:
                    result = None
            except Exception:
                result = None
            results.append(result)

        # print summary
        success = _summarize_result(
            results=results, nodes=nodes, test=test, call=call
        )
        if success:
            successful.append(test_name)

    print()
    rpc_bench.print_text_box('Equality Test Summary')
    print()
    rpc_bench.print_header('No differences detected (n = ' + str(len(successful)) + ')')
    if len(successful) == 0:
        print('[none]')
    else:
        for name in sorted(successful):
            rpc_bench.print_bullet(key=name, value='', colon_str='')
    print()

    failed = [test[0] for test in equality_tests if test[0] not in successful]
    rpc_bench.print_header('Differences detected (n = ' + str(len(failed)) + ')')
    if len(failed) == 0:
        print('[none]')
    else:
        for name in sorted(failed):
            rpc_bench.print_bullet(key=name, value='', colon_str='')


def json_equal(lhs: typing.Any, rhs: typing.Any) -> bool:
    import json

    return json.dumps(lhs, sort_keys=True) == json.dumps(rhs, sort_keys=True)


def _summarize_result(
    results: typing.Sequence[typing.Any],
    nodes: rpc_bench.Nodes,
    test: rpc_bench.EqualityTest,
    call: typing.Mapping[str, typing.Any],
) -> bool:
    import toolstr

    test_name, constructor, args, kwargs = test

    if not json_equal(results[0], results[1]):
        print()
        rpc_bench.print_text_box('Discrepancies in ' + test_name)
        print()
        rpc_bench.print_header('args')
        if len(args) > 0:
            for arg in args:
                rpc_bench.print_bullet(key=arg, value='', colon_str='')
        if len(kwargs) > 0:
            for key, value in kwargs.items():
                rpc_bench.print_bullet(key=key, value=value)
        print()
        rpc_bench.print_header('call')
        print(call)

        if any(result is None for result in results):
            print()
        for node, result in zip(nodes.values(), results):
            if result is None:
                toolstr.print(
                    node['name'] + ' failed', style=rpc_bench.styles['title']
                )

        if results[0] is None or results[1] is None:
            return False

        _print_result_diff(results=results, nodes=list(nodes.values()))

        return False

    else:
        return True


def _print_result_diff(
    results: typing.Sequence[typing.Any],
    nodes: typing.Sequence[rpc_bench.Node],
) -> None:
    import toolstr

    result0 = results[0]
    result1 = results[1]

    if type(result0) is not type(result1):
        for node, result in zip(nodes, results):
            print(node['name'], 'type:', type(result))
        return

    if isinstance(result0, dict):
        keys0 = set(result0.keys())
        keys1 = set(result1.keys())
        if keys0 != keys1:
            only_in_0 = keys0 - keys1
            only_in_1 = keys1 - keys0
            print()
            rpc_bench.print_header('different fields in results')
            if len(only_in_0) > 0:
                print(
                    '- present only in',
                    nodes[0]['name'] + ':',
                    ', '.join(only_in_0),
                )
            if len(only_in_1) > 0:
                print(
                    '- present only in',
                    nodes[1]['name'] + ':',
                    ', '.join(only_in_1),
                )

        rows = []
        for key in keys0 & keys1:
            if not json_equal(result0[key], result1[key]):
                row = [key, result0[key], result1[key]]
                rows.append(row)
        if len(rows) > 0:
            print()
            rpc_bench.print_header('differences in values')
            rpc_bench.print_table(
                rows,
                labels=['field', nodes[0]['name'], nodes[1]['name']],
                compact=3,
                max_column_widths=[20, 30, 30],
                indent=4,
            )

    elif isinstance(result0, list):
        if len(result1) != len(result0):
            print()
            rpc_bench.print_header('different number of results')
            for node, result in zip(nodes, results):
                rpc_bench.print_bullet(
                    key=node['name'], value=str(len(result)) + ' results'
                )
        else:
            raise NotImplementedError()

    else:
        if result1 != result0:
            rpc_bench.print_header('differences in values')
            for node, result in zip(nodes, results):
                rpc_bench.print_bullet(key=node['name'], value=result)

