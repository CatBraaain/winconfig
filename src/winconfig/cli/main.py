import json
from pathlib import Path
from typing import Annotated

import typer
import yaml

from winconfig.model.config import Config

app = typer.Typer()


@app.command()
def apply(
    path: Annotated[str, typer.Option()],
) -> None:
    print(yaml.safe_load(Path(path).read_text()))


@app.command()
def revert(
    path: Annotated[str, typer.Option()],
) -> None:
    print(yaml.safe_load(Path(path).read_text()))


@app.command()
def schema(
    output: Annotated[str, typer.Option()],
) -> None:
    schema = Config.model_json_schema()
    Path(output).write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    app()
