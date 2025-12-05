import json
from pathlib import Path
from typing import Annotated

import typer

from winconfig.engine.task_builder import TaskBuilder, TaskPlan

app = typer.Typer(
    no_args_is_help=True,
)


@app.command(no_args_is_help=True)
def apply(
    plan_path: Annotated[str, typer.Option()],
    extra_definition_paths: Annotated[list[str] | None, typer.Option()] = None,
) -> None:
    if extra_definition_paths is None:
        extra_definition_paths = []
    TaskBuilder(
        plan_path=plan_path,
        extra_definition_paths=extra_definition_paths,
    ).apply()


@app.command(no_args_is_help=True)
def schema(
    output: Annotated[str, typer.Option()],
) -> None:
    schema = TaskPlan.model_json_schema()
    Path(output).write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    app()
