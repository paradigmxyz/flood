import flood


def test_local_node_1(flood_test_local_node_1):
    result = flood.user_io.parse_node(flood_test_local_node_1)
    assert result['remote'] is None


def test_local_node_2(flood_test_local_node_2):
    result = flood.user_io.parse_node(flood_test_local_node_2)
    assert result['remote'] is None


def test_remote_node_1(flood_test_remote_node_1):
    result = flood.user_io.parse_node(flood_test_remote_node_1)
    assert result['remote'] is not None


def test_remote_node_2(flood_test_remote_node_2):
    result = flood.user_io.parse_node(flood_test_remote_node_2)
    assert result['remote'] is not None

