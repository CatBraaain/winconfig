import json

import typer

from winconfig.dsl.definition import Definition
from winconfig.engine.model_loader import ModelLoader
from winconfig.engine.task_builder import TaskBuilder, TaskPlan

from .cli_utils import (
    DryRunParam,
    ExtraDefinitionPathsParam,
    OutputParam,
    TaskPlanPathParam,
    generate_schema,
    handle_cli_error,
    handle_output,
)

app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
schema_command = typer.Typer()
app.add_typer(
    schema_command,
    name="schema",
    no_args_is_help=True,
    help="Generate JSON schemas.",
)


@app.command(
    no_args_is_help=True,
    help="Apply the specified task plan. You can also load additional definition files.",
)
def apply(
    task_plan_path: TaskPlanPathParam,
    extra_definition_paths: ExtraDefinitionPathsParam = None,
    dry_run: DryRunParam = False,
) -> None:
    if extra_definition_paths is None:
        extra_definition_paths = []
    with handle_cli_error():
        task_builder = TaskBuilder(
            task_plan_path=task_plan_path,
            extra_definition_paths=extra_definition_paths,
        )
        if not dry_run:
            task_builder.apply()


@schema_command.command(
    "taskplan",
    help="Output the JSON schema of TaskPlan.",
)
def generate_task_plan_schema(
    output: OutputParam = None,
    extra_definition_paths: ExtraDefinitionPathsParam = None,
) -> None:
    if extra_definition_paths is None:
        extra_definition_paths = []
    with handle_cli_error():
        schema_dict = generate_schema(TaskPlan)
        definition = ModelLoader.load_definitions(extra_definition_paths)
        schema_dict["propertyNames"] = {
            "enum": [td.name for td in definition.root],
            "type": "string",
        }
        schema = json.dumps(schema_dict, ensure_ascii=False, indent=2)
        handle_output(content=schema, output_path=output)


@schema_command.command(
    "definition",
    help="Output the JSON schema of Definition.",
)
def generate_definition_schema(
    output: OutputParam = None,
) -> None:
    with handle_cli_error():
        schema_dict = generate_schema(Definition)
        schema = json.dumps(schema_dict, ensure_ascii=False, indent=2)
        handle_output(content=schema, output_path=output)


if __name__ == "__main__":
    app()
