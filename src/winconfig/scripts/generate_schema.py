import json
from pathlib import Path
from typing import Any

from pydantic import ConfigDict
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue

from winconfig.model.definition import Definitions


class GenerateJsonSchemaNoTitles(GenerateJsonSchema):
    def field_title_should_be_set(self, schema: Any) -> bool:  # noqa: ANN401, ARG002
        return False

    def _update_class_schema(
        self, json_schema: JsonSchemaValue, cls: type[Any], config: ConfigDict
    ) -> None:
        super()._update_class_schema(json_schema, cls, config)
        json_schema.pop("title", None)


schema_json = Definitions.model_json_schema(schema_generator=GenerateJsonSchemaNoTitles)

Path("src/winconfig/definitions/schema.json").write_text(
    json.dumps(schema_json, indent=2) + "\n"
)
