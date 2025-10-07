import json
from pathlib import Path
from typing import Annotated

import typer
import yaml

from winconfig.cli.apply_tasks import apply_tasks
from winconfig.model.config import ConfigContainer
from winconfig.model.definition import DefinitionContainer

app = typer.Typer()


@app.command()
def apply(
    path: Annotated[str, typer.Option()],
) -> None:
    config_container = ConfigContainer.model_validate(
        yaml.safe_load(Path(path).read_text())
    )
    definition_container = DefinitionContainer.model_validate(
        yaml.safe_load(
            Path("src/winconfig/definitions/winutil_definitions.yaml").read_text()
        )
    )
    tasks = definition_container.generate_tasks(config_container)
    result = apply_tasks(tasks)


# @app.command()
# def revert(
#     path: Annotated[str, typer.Option()],
# ) -> None:
#     print(yaml.safe_load(Path(path).read_text()))


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
