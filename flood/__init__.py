"""tool for benchmarking RPC endpoints"""

from .generators import *
from .runners import *
from .spec import *
from .tests import *
from .user_io import *


__version__ = '0.2.5'


def _clean_package_imports() -> None:
    """remove deep nested modules from flood namespace"""

    import sys

    flood = sys.modules['flood']
    moduletype = type(flood)
    delattr(flood, 'annotations')
    for key, value in tuple(vars(flood).items()):
        if isinstance(value, moduletype):
            name = value.__name__
            if not name.startswith('flood') or name.count('.') > 1:
                delattr(flood, key)


_clean_package_imports()
