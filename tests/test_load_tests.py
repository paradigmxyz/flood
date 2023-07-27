import subprocess

import pytest

import flood


cmd_templates = {
    'local_bare': 'flood {test_name} {local_node_1} {local_node_2} -d 1 -r 1 2 4',  # noqa: E501
    # 'local_alias': 'flood {test_name} node1={local_node_1} node2={local_node_2} -d 1 -r 1 2 4',  # noqa: E501
    'remote_bare': 'flood {test_name} {remote_node_1} {remote_node_2} -d 1 -r 20 40 60',  # noqa: E501
    # 'remote_alias': 'flood {test_name} node1={remote_node_1} node2={remote_node_2} -d 1 -r 1 2 4',  # noqa: E501
}


@pytest.mark.parametrize(
    'test_name', flood.generators.get_single_test_generators().keys()
)
@pytest.mark.parametrize('cmd_template', cmd_templates.keys())
def test_load_test(
    test_name,
    cmd_template,
    flood_test_local_node_1,
    flood_test_local_node_2,
    flood_test_remote_node_1,
    flood_test_remote_node_2,
):
    cmd = cmd_templates[cmd_template].format(
        test_name=test_name,
        local_node_1=flood_test_local_node_1,
        local_node_2=flood_test_local_node_2,
        remote_node_1=flood_test_remote_node_1,
        remote_node_2=flood_test_remote_node_2,
    )
    subprocess.check_call(cmd.split(' '))

