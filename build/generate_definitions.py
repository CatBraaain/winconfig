import re
import subprocess
from pathlib import Path
from typing import Any

import httpx
import yaml
from winutil_definition import WinutilDefinitionContainer


def main() -> None:
    create_winutil_definitions()


def create_winutil_definitions() -> None:
    url = "https://raw.githubusercontent.com/ChrisTitusTech/winutil/refs/heads/main/config/tweaks.json"
    res = httpx.get(url)
    res.raise_for_status()

    valid_json = re.sub(
        r"(\"(?:InvokeScript|UndoScript)\": \[\n\s*[\"'])([\s\S]*?)([\"']\n\s*],?\n)",
        lambda x: x.group(1)
        + re.sub(r"(\n\r? {0,6})", r"\\n", x.group(2).lstrip())
        + x.group(3),
        res.text,
    )
    definitions = WinutilDefinitionContainer.model_validate(
        yaml.safe_load(valid_json)
    ).to_definitions()

    def str_presenter(dumper: Any, data: Any) -> Any:  # noqa: ANN401
        if len(data.splitlines()) > 1:
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    yaml.add_representer(str, str_presenter)

    schema_ref_str = "# yaml-language-server: $schema=./schema.json"
    yaml_str = (
        schema_ref_str
        + "\n\n"
        + yaml.dump(
            definitions.model_dump(exclude_defaults=True),
            allow_unicode=True,
            sort_keys=False,
        )
    )

    dist = "src/winconfig/definitions/winutil_definition.yaml"
    Path(dist).write_text(yaml_str, encoding="utf-8")
    subprocess.run(["bunx", "prettier", "--write", f'"{dist}"'], check=True)


main()
