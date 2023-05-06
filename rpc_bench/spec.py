from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import toolcli

    MethodCalls = typing.Mapping[str, typing.Sequence[typing.Any]]

    NodeMethodLatencies = typing.Mapping[
        str, typing.Mapping[str, typing.Sequence[str]]
    ]

    class LatencyBenchmarkResults(typing.TypedDict):
        nodes: typing.Mapping[str, str]
        methods: typing.Sequence[str]
        samples: int | None
        calls: typing.Mapping[str, typing.Sequence[str]]
        latencies: NodeMethodLatencies

    class ProgressBar(typing.TypedDict):
        desc: str
        position: int
        leave: bool
        colour: str
        disable: bool


styles: toolcli.StyleTheme = {
    'title': 'bold #00e100',
    'metavar': 'bold #e5e9f0',
    'description': '#aaaaaa',
    'content': '#00B400',
    'option': 'bold #e5e9f0',
    'comment': '#888888',
}

