import json
import subprocess
from pathlib import Path
from typing import Any

import yaml
from pydantic import ConfigDict
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue

from winconfig.cli.config import ConfigFile
from winconfig.models.definition import Definition


def main() -> None:
    generate_definition_schema()
    generate_config_schema()


class GenerateJsonSchemaNoTitles(GenerateJsonSchema):
    def field_title_should_be_set(self, schema: Any) -> bool:  # noqa: ANN401, ARG002
        return False

    def _update_class_schema(
        self, json_schema: JsonSchemaValue, cls: type[Any], config: ConfigDict
    ) -> None:
        super()._update_class_schema(json_schema, cls, config)
        json_schema.pop("title", None)


def generate_definition_schema() -> None:
    schema_json = Definition.model_json_schema(
        schema_generator=GenerateJsonSchemaNoTitles
    )

    dist = "./src/winconfig/definitions/builtin.definition.schema.json"
    Path(dist).write_text(json.dumps(schema_json, indent=2) + "\n")
    subprocess.run(["bunx", "prettier", "--write", f'"{dist}"'], check=True)


def generate_taskname_type() -> None:
    src = "./src/winconfig/definitions/builtin.definition.yaml"
    definition = Definition.model_validate(yaml.safe_load(Path(src).read_text()))
    task_names = [td.name for td in definition.root]
    taskname_file = "./src/winconfig/definitions/builtin_taskname.py"
    taskname_script = (
        "from typing import Literal\n"
        f"type TaskName = Literal[{''.join([f'"{task_name}",' for task_name in task_names])}]"
    )
    Path(taskname_file).write_text(taskname_script)
    subprocess.run(["uv", "run", "ruff", "format", taskname_file], check=True)


def generate_config_schema() -> None:
    schema_json = ConfigFile.model_json_schema(
        schema_generator=GenerateJsonSchemaNoTitles
    )

    dist = "./winconfig.config.schema.json"
    Path(dist).write_text(json.dumps(schema_json, indent=2) + "\n")
    subprocess.run(["bunx", "prettier", "--write", f'"{dist}"'], check=True)


main()
