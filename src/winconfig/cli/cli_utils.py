from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import typer


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
