from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Any

import typer

OutputParam = Annotated[
    str | None,
    typer.Option(
        help="Path to the file where the schema will be saved.",
    ),
]
TaskPlanPathParam = Annotated[
    Path,
    typer.Argument(
        help="Path to the task plan to apply.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
]
ExtraDefinitionPathsParam = Annotated[
    list[Path] | None,
    typer.Option(
        *["-e", "--extra_definition_paths"],
        help=(
            "Path to an additional definition file. "
            "Can be specified multiple times to include multiple files. "
            "If the same definition exists, the last one specified overrides the previous ones."
        ),
    ),
]
DryRunParam = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Do not apply any changes. Useful for validating the task plan and definitions without executing them.",
    ),
]


@contextmanager
def handle_cli_error() -> Generator[None, Any, None]:
    try:
        yield
    except Exception as e:
        typer.echo(typer.style("Error: ", fg=typer.colors.RED, bold=True) + str(e))


def handle_output(content: str, output_path: str | None) -> None:
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        typer.echo(content)
