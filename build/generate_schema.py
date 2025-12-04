import json
import subprocess
from pathlib import Path
from typing import Any

import yaml
from pydantic import ConfigDict
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue

from winconfig.dsl.definition import Definition
from winconfig.engine.task_builder import TaskPlan


def main() -> None:
    generate_definition_schema()
    generate_plan_schema()


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

    dist = "./src/winconfig/resources/builtin.definition.schema.json"
    Path(dist).write_text(json.dumps(schema_json, indent=2) + "\n")
    subprocess.run(["bunx", "prettier", "--write", f'"{dist}"'], check=True)


def generate_plan_schema() -> None:
    src = "./src/winconfig/resources/builtin.definition.yaml"
    definition = Definition.model_validate(yaml.safe_load(Path(src).read_text()))
    task_names = [td.name for td in definition.root]

    schema_json = TaskPlan.model_json_schema(
        schema_generator=GenerateJsonSchemaNoTitles
    )
    schema_json["propertyNames"] = {
        "enum": task_names,
        "type": "string",
    }

    dist = "./winconfig.tasks.schema.json"
    Path(dist).write_text(json.dumps(schema_json, indent=2) + "\n")
    subprocess.run(["bunx", "prettier", "--write", f'"{dist}"'], check=True)


main()
