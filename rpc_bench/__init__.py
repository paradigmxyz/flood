"""tool for benchmarking RPC endpoints"""

from .generators import *
from .spec import *
from .tests import *
from .user_io import *


__version__ = '0.1.0'


def _clean_package_imports() -> None:
    """remove deep nested modules from rpc_bench namespace"""

    import sys

    rpc_bench = sys.modules['rpc_bench']
    moduletype = type(rpc_bench)
    delattr(rpc_bench, 'annotations')
    for key, value in tuple(vars(rpc_bench).items()):
        if isinstance(value, moduletype):
            name = value.__name__
            if not name.startswith('rpc_bench') or name.count('.') > 1:
                delattr(rpc_bench, key)


_clean_package_imports()
