import subprocess


def test_equality_tests(flood_test_local_node_1, flood_test_local_node_2):
    cmd = 'flood all node1={} node2={} --equality'.format(
        flood_test_local_node_1,
        flood_test_local_node_2,
    )
    subprocess.check_call(cmd.split(' '))

