import re
from pathlib import Path
from typing import Any

import httpx
import yaml


def main() -> None:
    create_winutil_tasks()


def create_winutil_tasks() -> None:
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

    config_task_dict = yaml.safe_load(valid_json)
    config_tasks = [
        {
            "name": name.replace("WPF", ""),
            "description": config_task["Description"],
            "registries": [
                {
                    "path": registry["Path"],
                    "name": registry["Name"],
                    "type": registry["Type"],
                    "old_value": registry["OriginalValue"],
                    "new_value": registry["Value"],
                }
                for registry in config_task.get("registry", [])
            ],
            "scheduled_tasks": [
                {
                    "path": registry["Name"],
                    "old_state": registry["OriginalState"].lower(),
                    "new_state": registry["State"].lower(),
                }
                for registry in config_task.get("ScheduledTask", [])
            ],
            "services": [
                {
                    "name": registry["Name"],
                    "old_startup_type": registry["OriginalType"],
                    "new_startup_type": registry["StartupType"],
                }
                for registry in config_task.get("service", [])
            ],
            "script": {
                "apply": "\n".join(config_task.get("InvokeScript", [])).rstrip()
                or None,
                "revert": "".join(config_task.get("UndoScript", [])).rstrip() or None,
            }
            if config_task.get("InvokeScript")
            else None,
        }
        for name, config_task in config_task_dict.items()
        if config_task.get("Description")
    ]
    config_tasks = [
        {key: value for key, value in config_task.items() if value}
        for config_task in config_tasks
    ]

    def str_presenter(dumper: Any, data: Any) -> Any:  # noqa: ANN401
        if len(data.splitlines()) > 1:
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    yaml.add_representer(str, str_presenter)

    schema_ref_str = "# yaml-language-server: $schema=./schema.json"
    yaml_str = (
        schema_ref_str
        + "\n\n"
        + yaml.dump(config_tasks, allow_unicode=True, sort_keys=False)
    )

    Path("config_tasks/winutil_tasks.yaml").write_text(yaml_str, encoding="utf-8")


main()
