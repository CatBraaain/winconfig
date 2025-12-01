import json
from pathlib import Path
from typing import Annotated

import typer

from winconfig.cli.config import ConfigContainer
from winconfig.cli.config_applier import ConfigApplier

app = typer.Typer()


@app.command()
def apply(
    path: Annotated[str, typer.Option()],
) -> None:
    ConfigApplier(config_path=path).apply(mode="apply")


@app.command()
def revert(
    path: Annotated[str, typer.Option()],
) -> None:
    ConfigApplier(config_path=path).apply(mode="revert")


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
