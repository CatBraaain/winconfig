import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Any, Literal

import typer
from loguru import logger
from pydantic import BaseModel, ConfigDict, RootModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue

OutputParam = Annotated[
    str | None,
    typer.Option(
        help="Path to the file where the schema will be saved.",
    ),
]
ConfigPathParams = Annotated[
    list[Path],
    typer.Argument(
        default_factory=list,
        help="Path(s) to the config file(s). Later files override earlier ones.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
]
DryRunParam = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Do not apply any changes. Useful for validating the config file without executing them.",
    ),
]


def loglevel_callback(
    loglevel: Annotated[
        Literal["DEBUG", "INFO", "WARNING", "ERROR", "SILENT"],
        typer.Option(help="Set the logging level"),
    ] = "INFO",
) -> None:
    if loglevel == "SILENT":
        logger.remove()
    else:
        logger.configure(
            handlers=[
                {
                    "sink": sys.stderr,
                    "format": "<green>{time:HH:mm:ss.SSS}</green> | <level>{message}</level>",
                    "level": loglevel,
                }
            ]  # ty:ignore[invalid-argument-type]  # loguru not having runtime type
        )
    logger.debug(f"Log level: {loglevel}")


LogLevelParam = Annotated[
    Literal["DEBUG", "INFO", "WARNING", "ERROR", "SILENT"],
    typer.Option(help="Set the logging level", callback=loglevel_callback),
]


@contextmanager
def handle_cli_error() -> Generator[None, Any, None]:
    try:
        yield
    except Exception as e:
        logger.error(str(e))


def handle_output(content: str, output_path: str | None) -> None:
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        typer.echo(content)


class GenerateJsonSchemaNoTitles(GenerateJsonSchema):
    def field_title_should_be_set(self, schema: Any) -> bool:  # noqa: ANN401, ARG002
        return False

    def _update_class_schema(
        self, json_schema: JsonSchemaValue, cls: type[Any], config: ConfigDict
    ) -> None:
        super()._update_class_schema(json_schema, cls, config)
        json_schema.pop("title", None)


def generate_schema(model_type: type[BaseModel | RootModel]) -> dict[str, Any]:
    return model_type.model_json_schema(schema_generator=GenerateJsonSchemaNoTitles)
