import json
from pathlib import Path
from typing import Annotated

import typer

from winconfig.engine.task_builder import TaskBuilder, TaskPlan

app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command(no_args_is_help=True)
def apply(
    task_plan_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    extra_definition_paths: Annotated[
        list[Path],
        typer.Option(
            *["-e", "--extra_definition_paths"],
            default_factory=list,
        ),
    ],
) -> None:
    TaskBuilder(
        task_plan_path=task_plan_path,
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
