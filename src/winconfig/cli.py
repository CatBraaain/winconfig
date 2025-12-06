import json
from pathlib import Path
from typing import Annotated

import typer

from winconfig.engine.task_builder import TaskBuilder, TaskPlan

app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command(
    no_args_is_help=True,
    help="Apply the specified task plan. You can also load additional definition files.",
)
def apply(
    task_plan_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the task plan to apply.",
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
            help=(
                "Path to an additional definition file. "
                "Can be specified multiple times to include multiple files. "
                "If the same definition exists, the last one specified overrides the previous ones."
            ),
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Do not apply any changes. Useful for validating the task plan and definitions without executing them.",
        ),
    ] = False,
) -> None:
    try:
        task_builder = TaskBuilder(
            task_plan_path=task_plan_path,
            extra_definition_paths=extra_definition_paths,
        )
        if not dry_run:
            task_builder.apply()
    except Exception as e:
        typer.echo(typer.style("Error: ", fg=typer.colors.RED, bold=True) + str(e))


@app.command(
    help="Output the JSON schema of TaskPlan.",
)
def schema(
    output: Annotated[
        str | None,
        typer.Option(
            help="Path to the file where the schema will be saved.",
        ),
    ] = None,
) -> None:
    schema_dict = TaskPlan.model_json_schema()
    schema = json.dumps(schema_dict, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(schema, encoding="utf-8")
    else:
        typer.echo(schema)


if __name__ == "__main__":
    app()
