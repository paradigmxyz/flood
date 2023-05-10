from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import toolcli

    # class Call(typing.TypedDict):
    #     jsonrpc: typing.Literal['2.0']
    #     method: str
    #     params: typing.Sequence[typing.Any]
    #     id: int
    Call = typing.Mapping[str, typing.Any]

    MethodCalls = typing.Mapping[str, typing.Sequence[typing.Any]]

    class Node(typing.TypedDict):
        name: str
        url: str
        remote: str | None

    NodesShorthand = typing.Union[
        typing.Sequence[str],
        typing.Sequence[Node],
        typing.Mapping[str, str],
        typing.Mapping[str, Node],
    ]

    NodeMethodLatencies = typing.Mapping[str, typing.Sequence[float]]
    NodesMethodLatencies = typing.Mapping[str, NodeMethodLatencies]

    class LatencyBenchmarkResults(typing.TypedDict):
        nodes: typing.Mapping[str, Node]
        methods: typing.Sequence[str]
        samples: int | None
        calls: typing.Mapping[str, typing.Sequence[str]]
        latencies: NodesMethodLatencies

    class ProgressBar(typing.TypedDict):
        desc: str
        position: int | None
        leave: bool
        colour: str
        disable: bool

    class Test(typing.TypedDict):
        url: str
        rates: typing.Sequence[int]
        duration: int
        calls: typing.Sequence[typing.Any]


styles: toolcli.StyleTheme = {
    'title': 'bold #00e100',
    'metavar': 'bold #e5e9f0',
    'description': '#aaaaaa',
    'content': '#00B400',
    'option': 'bold #e5e9f0',
    'comment': '#888888',
}

