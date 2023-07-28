"""generic functions for creating notebooks"""
from __future__ import annotations

import typing

import nbformat


if typing.TYPE_CHECKING:

    class NotebookCellTemplateContent(typing.TypedDict):
        type: typing.Literal['markdown', 'code']
        content: str
        inputs: typing.Sequence[str]

    class NotebookCellTemplateFunction(typing.TypedDict):
        type: typing.Literal['markdown', 'code']
        f: typing.Callable[..., str]
        inputs: typing.Sequence[str]

    NotebookCellTemplate = typing.Union[
        NotebookCellTemplateContent,
        NotebookCellTemplateFunction,
    ]

    class NotebookChunkTemplate(typing.TypedDict):
        type: typing.Literal['chunk']
        f: typing.Callable[
            ..., typing.Sequence[nbformat.notebooknode.NotebookNode]
        ]
        inputs: typing.Sequence[str]

    NotebookCellPrecursor = typing.Union[
        NotebookCellTemplate,
        NotebookChunkTemplate,
        nbformat.notebooknode.NotebookNode,
    ]
    NotebookTemplate = typing.Sequence[NotebookCellPrecursor]


def create_cell(
    cell_template: NotebookCellTemplate,
    inputs: typing.Mapping[str, typing.Any],
) -> nbformat.notebooknode.NotebookNode:
    # create cell content
    if 'content' in cell_template:
        content = cell_template['content']  # type: ignore
        if 'inputs' in cell_template:
            format_inputs = {
                input: inputs[input] for input in cell_template['inputs']
            }
            content = content.format(**format_inputs)
    elif 'f' in cell_template:
        f_inputs = {input: inputs[input] for input in cell_template['inputs']}
        content = cell_template['f'](**f_inputs)
    else:
        raise Exception('invalid cell format')

    # left justify as needed
    lines = content.split('\n')
    if lines[0] == '':
        left_spaces = [
            len(line) - len(line.lstrip(' '))
            for line in lines
            if not set(line).issubset({' '})
        ]
        cut = min(left_spaces[:])
        content = '\n'.join(line[cut:] for line in lines)

    content = content.strip()

    # create cell object
    cell_obj: nbformat.notebooknode.NotebookNode
    if cell_template['type'] == 'markdown':
        cell_obj = nbformat.v4.new_markdown_cell(source=content)  # type: ignore
    elif cell_template['type'] == 'code':
        cell_obj = nbformat.v4.new_code_cell(source=content)  # type: ignore
    else:
        raise Exception('invalid cell type')

    return cell_obj


def create_cell_chunk(
    chunk_template: NotebookChunkTemplate,
    inputs: typing.Mapping[str, typing.Any],
) -> typing.Sequence[nbformat.notebooknode.NotebookNode]:
    if 'f' in chunk_template:
        chunk_inputs = {
            input: inputs[input] for input in chunk_template['inputs']
        }
        cell_templates = chunk_template['f'](**chunk_inputs)
    else:
        raise Exception('invalid chunk template format')

    return create_cells(cell_templates=cell_templates, inputs=inputs)


def create_cells(
    cell_templates: typing.Sequence[NotebookCellPrecursor],
    inputs: typing.Mapping[str, typing.Any],
) -> typing.Sequence[nbformat.notebooknode.NotebookNode]:
    cell_objs = []
    for cell_template in cell_templates:
        if isinstance(cell_template, nbformat.notebooknode.NotebookNode):
            cell_objs.append(cell_template)
        elif cell_template['type'] == 'chunk':
            cell_objs += create_cell_chunk(
                chunk_template=cell_template,
                inputs=inputs,
            )
        else:
            cell_obj = create_cell(
                cell_template=cell_template,
                inputs=inputs,
            )
            cell_objs.append(cell_obj)
    return cell_objs


def create_notebook(
    cell_templates: NotebookTemplate,
    output_path: str,
    inputs: typing.Mapping[str, typing.Any] | None = None,
) -> None:
    # create cells
    if inputs is None:
        inputs = {}
    cells = create_cells(cell_templates=cell_templates, inputs=inputs)

    # create notebook object
    notebook = nbformat.v4.new_notebook()  # type: ignore
    notebook['cells'] = cells

    # write notebook to file
    with open(output_path, 'w') as f:
        nbformat.write(notebook, f)  # type: ignore
