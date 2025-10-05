from pathlib import Path
from typing import Annotated

import typer
import yaml

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


if __name__ == "__main__":
    app()
