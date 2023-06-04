import os

import pytest


def get_env_value(name):
    value = os.environ.get(name)
    if value in [None, '']:
        raise Exception(name + ' not set')
    return value


@pytest.fixture
def flood_test_local_node_1():
    return get_env_value('FLOOD_TEST_LOCAL_NODE_1')


@pytest.fixture
def flood_test_local_node_2():
    return get_env_value('FLOOD_TEST_LOCAL_NODE_2')


@pytest.fixture
def flood_test_remote_node_1():
    return get_env_value('FLOOD_TEST_REMOTE_NODE_1')


@pytest.fixture
def flood_test_remote_node_2():
    return get_env_value('FLOOD_TEST_REMOTE_NODE_2')

