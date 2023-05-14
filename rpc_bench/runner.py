from __future__ import annotations

import typing

from . import spec


# def run(
#     test_name: spec.LoadTest,
#     *,
#     mode: spec.Mode = 'stress',
#     nodes: spec.NodesShorthand,
#     random_seed: spec.RandomSeed | None = None,
#     verbose: bool,
#     rates: typing.Sequence[int] | None = None,
#     duration: int | None = None,
#     dry: bool,
#     output=output,
# ) -> None:
#     """generate and run load test(s) against node(s)"""

#     import os
#     import tempfile

#     if rates is None:
#         pass
#     if duration is None:
#         pass

#     tests = generate_tests(
#         test=test,
#     )

#     # parse output directory
#     if output is None:
#         output = tempfile.mkdtemp()
#     if not os.path.isdir(output):
#         if os.path.exists(output):
#             raise Exception()
#         else:
#             os.makedirs(output)

#     if not dry:
#         pass

