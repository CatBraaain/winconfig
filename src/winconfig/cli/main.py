import json
from pathlib import Path
from typing import Annotated

import typer

from winconfig.cli.config import ConfigFile, WinConfig

app = typer.Typer()


@app.command()
def apply(
    path: Annotated[str, typer.Option()],
) -> None:
    WinConfig(config_path=path).apply()


@app.command()
def schema(
    output: Annotated[str, typer.Option()],
) -> None:
    schema = ConfigFile.model_json_schema()
    Path(output).write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    app()
