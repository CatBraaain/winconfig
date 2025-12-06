from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import typer


@contextmanager
def handle_cli_error() -> Generator[None, Any, None]:
    try:
        yield
    except Exception as e:
        typer.echo(typer.style("Error: ", fg=typer.colors.RED, bold=True) + str(e))
