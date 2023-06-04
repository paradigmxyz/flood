from __future__ import annotations

import typing

import flood
from . import equality_test_sets


def run_equality_test(
    test_name: str,
    nodes: flood.NodesShorthand,
    *,
    verbose: bool | int = True,
    random_seed: flood.RandomSeed | None = None,
    output_dir: str | None = None,
) -> None:
    import json
    import os
    import requests
    import toolstr

    nodes = flood.parse_nodes(nodes, request_metadata=True)
    for node in nodes.values():
        if node['remote'] is not None:
            raise Exception('remote not supported for equality test')
    if len(nodes) != 2:
        raise Exception('should use two nodes in equality test')

    # get tests
    if test_name != 'all':
        raise NotImplementedError('must use test_name="all" for equality test')
    equality_tests = equality_test_sets.get_all_equality_tests()

    if output_dir is None:
        import tempfile

        output_dir = tempfile.mkdtemp()

    # print preamble
    flood.print_text_box('Equality test: ' + test_name)
    flood.print_bullet(key='methods', value='')
    for test in equality_tests:
        flood.print_bullet(key=test[0], value='', colon_str='', indent=4)
    flood.print_bullet(key='output_dir', value=output_dir)
    flood.print_bullet(key='nodes', value='')
    for n, node in enumerate(nodes.values()):
        toolstr.print(
            toolstr.add_style(str(n + 1), flood.styles['metavar'])
            + '. '
            + str(node),
            indent=4,
            style=flood.styles['description'],
        )

    # run test
    successful = []
    calls = {}
    call_node_responses: typing.Any = {}
    headers = {'Content-Type': 'application/json', 'User-Agent': 'flood'}
    for test in equality_tests:
        # create call
        test_name, constructor, args, kwargs = test
        call = constructor(*args, **kwargs)
        calls[test_name] = call
        call_node_responses.setdefault(test_name, {})

        # dispatch call
        results = []
        responses = []
        for node in nodes.values():
            response = None
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
            responses.append(response)
            results.append(result)
            call_node_responses[test_name][node['name']] = result

        # print summary
        success = _summarize_result(
            responses=responses,
            results=results,
            nodes=nodes,
            test=test,
            call=call,
        )
        if success:
            successful.append(test_name)
    failed = [test[0] for test in equality_tests if test[0] not in successful]

    # save output file
    summary = {
        'calls': calls,
        'successful': successful,
        'failed': failed,
        'responses': call_node_responses,
    }
    file_path = os.path.join(output_dir, 'equality_results.json')
    with open(file_path, 'w') as f:
        json.dump(summary, f)

    # summarize test
    print()
    flood.print_text_box('Equality Test Summary')
    print()
    flood.print_header(
        'No differences detected (n = ' + str(len(successful)) + ')'
    )
    if len(successful) == 0:
        print('[none]')
    else:
        for name in sorted(successful):
            flood.print_bullet(key=name, value='', colon_str='')
    print()
    flood.print_header('Differences detected (n = ' + str(len(failed)) + ')')
    if len(failed) == 0:
        print('[none]')
    else:
        for name in sorted(failed):
            flood.print_bullet(key=name, value='', colon_str='')
    print()
    toolstr.print(
        'summary saved to: ' + file_path, style=flood.styles['comment']
    )


def _json_equal(lhs: typing.Any, rhs: typing.Any) -> bool:
    import json

    return json.dumps(lhs, sort_keys=True) == json.dumps(rhs, sort_keys=True)


def _summarize_result(
    responses: typing.Sequence[typing.Any],
    results: typing.Sequence[typing.Any],
    nodes: flood.Nodes,
    test: flood.EqualityTest,
    call: typing.Mapping[str, typing.Any],
) -> bool:
    import toolstr

    test_name, constructor, args, kwargs = test

    if not _json_equal(results[0], results[1]):
        print()
        flood.print_text_box('Discrepancies in ' + test_name)
        print()
        flood.print_header('args')
        if len(args) > 0:
            for arg in args:
                flood.print_bullet(key=arg, value='', colon_str='')
        if len(kwargs) > 0:
            for key, value in kwargs.items():
                flood.print_bullet(key=key, value=value)
        print()
        flood.print_header('call')
        print(call)

        if any(result is None for result in results):
            print()
        for node, result, response in zip(nodes.values(), results, responses):
            if result is None:
                toolstr.print(
                    node['name'] + ' failed', style=flood.styles['title']
                )
                if response.status_code == 200:
                    print('response:', response.json())
                else:
                    print('response: status code ', response.status_code)

        if results[0] is None or results[1] is None:
            return False

        _print_result_diff(results=results, nodes=list(nodes.values()))

        return False

    else:
        return True


def _print_result_diff(
    results: typing.Sequence[typing.Any],
    nodes: typing.Sequence[flood.Node],
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
            flood.print_header('different fields in results')
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
            if not _json_equal(result0[key], result1[key]):
                row = [key, result0[key], result1[key]]
                rows.append(row)
        if len(rows) > 0:
            print()
            flood.print_header('differences in values')
            flood.print_table(
                rows,
                labels=['field', nodes[0]['name'], nodes[1]['name']],
                compact=3,
                max_column_widths=[20, 30, 30],
                indent=4,
            )

    elif isinstance(result0, list):
        if len(result1) != len(result0):
            print()
            flood.print_header('different number of results')
            for node, result in zip(nodes, results):
                flood.print_bullet(
                    key=node['name'], value=str(len(result)) + ' results'
                )
        else:
            import json

            print('differences:')
            n_printed = 0
            for i, (item0, item1) in enumerate(zip(result0, result1)):
                if not _json_equal(item0, item1):
                    if n_printed >= 10:
                        print('...')
                        break

                    item0_str = json.dumps(item0)
                    if len(item0_str) > 20:
                        item0_str = item0_str[:17] + '...'
                    item1_str = json.dumps(item1)
                    if len(item1_str) > 20:
                        item1_str = item1_str[:17] + '...'
                    print('- item at index', i)
                    print('    -', nodes[0]['name'] + ':', item0_str)
                    print('    -', nodes[1]['name'] + ':', item1_str)

                    n_printed += 1

    else:
        if result1 != result0:
            flood.print_header('differences in values')
            for node, result in zip(nodes, results):
                flood.print_bullet(key=node['name'], value=result)
