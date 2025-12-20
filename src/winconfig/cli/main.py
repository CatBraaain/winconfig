import json

import typer

from winconfig.cli.cli_utils import (
    ConfigPathsParam,
    DryRunParam,
    LogLevelParam,
    OutputParam,
    generate_schema,
    handle_cli_error,
    handle_output,
)
from winconfig.config.config import Config
from winconfig.engine import Engine

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
    config_paths: ConfigPathsParam,
    reverse: bool = False,
    dry_run: DryRunParam = False,
    loglevel: LogLevelParam = "INFO",  # noqa: ARG001
) -> None:
    with handle_cli_error():
        engine = Engine(*config_paths)
        if not dry_run:
            engine.run(reverse=reverse)


@app.command(
    help="Output the JSON schema of Config. Use --strict to enforce strict action names."
)
def schema(
    config_paths: ConfigPathsParam,
    output: OutputParam = None,
    strict: bool = False,
    loglevel: LogLevelParam = "INFO",  # noqa: ARG001
) -> None:
    with handle_cli_error():
        schema_dict = generate_schema(Config)
        engine = Engine(*config_paths, validate=False)
        additional_props = not strict
        schema_dict["properties"]["Actions"] = {
            "properties": {
                task_group.name: {
                    "type": "object",
                    "properties": {
                        task.name: {"$ref": "#/$defs/ActionMode"}
                        for task in task_group.tasks
                    },
                    "additionalProperties": additional_props,
                }
                for task_group in engine.groups
            },
            "additionalProperties": additional_props,
        }
        schema = json.dumps(schema_dict, ensure_ascii=False, indent=2)
        handle_output(content=schema, output_path=output)


if __name__ == "__main__":
    app()
