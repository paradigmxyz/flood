"""tool for benchmarking RPC endpoints"""
# ruff: noqa: F401

from .spec import *
import flood.generators
import flood.ops
import flood.runners
import flood.tests
import flood.user_io

from flood.generators import generate_test
from flood.ops import get_flood_version
from flood.ops import get_local_installation
from flood.ops import get_remote_installation
from flood.ops import get_dependency_versions
from flood.runners import load_single_run_test_payload
from flood.runners import load_single_run_results_payload
from flood.runners import run
from flood.tests.equality_tests import run_equality_test
from flood.tests.load_tests import run_load_test
from flood.tests.load_tests import run_load_tests


__version__ = '0.3.0'


def _clean_package_imports() -> None:
    """remove deep nested modules from flood namespace"""

    import sys

    flood_module = sys.modules['flood']
    moduletype = type(flood)
    delattr(flood, 'annotations')
    for key, value in tuple(vars(flood_module).items()):
        if isinstance(value, moduletype):
            name = value.__name__
            if not name.startswith('flood') or name.count('.') > 1:
                delattr(flood, key)


_clean_package_imports()
