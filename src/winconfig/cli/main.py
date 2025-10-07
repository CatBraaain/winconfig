import json
from pathlib import Path
from typing import Annotated

import typer

from winconfig.cli.apply_tasks import apply_config
from winconfig.model.config import ConfigContainer

app = typer.Typer()


@app.command()
def apply(
    path: Annotated[str, typer.Option()],
) -> None:
    apply_config(path, mode="auto")


@app.command()
def revert(
    path: Annotated[str, typer.Option()],
) -> None:
    apply_config(path, mode="revert")


@app.command()
def schema(
    output: Annotated[str, typer.Option()],
) -> None:
    schema = ConfigContainer.model_json_schema()
    Path(output).write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    app()
