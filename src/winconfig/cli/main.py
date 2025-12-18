import json

import typer

from winconfig.cli.cli_utils import (
    ConfigPathParams,
    DryRunParam,
    LogLevelParam,
    OutputParam,
    generate_schema,
    handle_cli_error,
    handle_output,
)
from winconfig.dsl.config import Config
from winconfig.engine.config_context import ConfigContext

app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_show_locals=False,
)


@app.command(
    no_args_is_help=True,
    help="Run the configured actions.",
)
def run(
    config_paths: ConfigPathParams,
    reverse: bool = False,
    dry_run: DryRunParam = False,
    loglevel: LogLevelParam = "INFO",  # noqa: ARG001
) -> None:
    with handle_cli_error():
        config_context = ConfigContext.init(*config_paths)
        if not dry_run:
            config_context.run(reverse=reverse)


@app.command(
    help="Output the JSON schema of Config.",
)
def schema(
    output: OutputParam = None,
    loglevel: LogLevelParam = "INFO",  # noqa: ARG001
) -> None:
    with handle_cli_error():
        schema_dict = generate_schema(Config)
        builtin_config_context = ConfigContext.init()
        schema_dict["properties"]["Actions"]["properties"] = {
            task_group.name: {
                "type": "object",
                "properties": {
                    task.name: {"$ref": "#/$defs/ActionMode"}
                    for task in task_group.tasks
                },
                "additionalProperties": True,
            }
            for task_group in builtin_config_context.groups
        }
        schema_dict["properties"]["Actions"]["additionalProperties"] = True
        schema = json.dumps(schema_dict, ensure_ascii=False, indent=2)
        handle_output(content=schema, output_path=output)


if __name__ == "__main__":
    app()
