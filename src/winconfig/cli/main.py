import json

import typer

from winconfig.cli.cli_utils import (
    ConfigPathParam,
    DryRunParam,
    LogLevelParam,
    OutputParam,
    generate_schema,
    handle_cli_error,
    handle_output,
)
from winconfig.dsl.config import Config
from winconfig.engine.model_loader import ModelLoader
from winconfig.engine.task_builder import TaskBuilder

app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_show_locals=False,
)


@app.command(
    no_args_is_help=True,
    help="Apply the specified task plan. You can also load additional definition files.",
)
def apply(
    config_path: ConfigPathParam,
    reverse: bool = False,
    dry_run: DryRunParam = False,
    loglevel: LogLevelParam = "INFO",  # noqa: ARG001
) -> None:
    with handle_cli_error():
        task_builder = TaskBuilder(config_path=config_path)
        if not dry_run:
            task_builder.apply(reverse=reverse)


@app.command(
    help="Output the JSON schema of Config.",
)
def schema(
    output: OutputParam = None,
    loglevel: LogLevelParam = "INFO",  # noqa: ARG001
) -> None:
    with handle_cli_error():
        schema_dict = generate_schema(Config)
        builtin_definition = ModelLoader.load_configs([]).definition
        schema_dict["properties"]["Plan"]["properties"] = {
            task_group_name: {
                "type": "object",
                "properties": {
                    task_name: {"$ref": "#/$defs/TaskMode"} for task_name in task_group
                },
                "additionalProperties": True,
            }
            for task_group_name, task_group in builtin_definition.root.items()
        }
        schema_dict["properties"]["Plan"]["additionalProperties"] = True
        schema = json.dumps(schema_dict, ensure_ascii=False, indent=2)
        handle_output(content=schema, output_path=output)


if __name__ == "__main__":
    app()
