import re
import subprocess
from pathlib import Path
from typing import Any, Literal, Self

import httpx
import yaml
from capitalize import capitalize
from pydantic import BaseModel, ConfigDict

from winconfig.model.definition import (
    Definition,
    DefinitionContainer,
    Registry,
    RegistryValueKind,
    ScheduledTask,
    Script,
    Service,
    ServiceStartupType,
)
from winconfig.powershell.constants import NOT_EXIST


class WinutilRegistry(BaseModel):
    Path: str
    Name: str
    Type: RegistryValueKind
    OriginalValue: str
    Value: str


class WinutilScheduledTask(BaseModel):
    Name: str
    OriginalState: Literal["Enabled", "Disabled"]
    State: Literal["Enabled", "Disabled"]


class WinutilService(BaseModel):
    Name: str
    OriginalType: ServiceStartupType
    StartupType: ServiceStartupType


class WinutilDefinition(BaseModel):
    Content: str
    Description: str = ""
    registry: list[WinutilRegistry] = []
    ScheduledTask: list[WinutilScheduledTask] = []
    service: list[WinutilService] = []
    InvokeScript: list[str] | None = None
    UndoScript: list[str] | None = None

    Type: Any | None = None
    Order: Any | None = None
    panel: Any | None = None
    category: Any | None = None
    link: Any | None = None
    ButtonWidth: Any | None = None
    appx: Any | None = None
    Checked: Any | None = None
    ComboItems: Any | None = None

    model_config = ConfigDict(extra="forbid")


class WinutilDefinitionContainer(BaseModel):
    definition_dict: dict[str, WinutilDefinition]
    preload: str | None = None

    @classmethod
    def from_winutil_url(
        cls, definition_url: str, preload_script_urls: list[str]
    ) -> Self:
        res = httpx.get(definition_url)
        invalid_json = res.text
        fixed_json = re.sub(
            r"(\"(?:InvokeScript|UndoScript)\": \[\n\s*[\"'])([\s\S]*?)([\"']\n\s*],?\n)",
            lambda x: x.group(1)
            + re.sub(r"(\n\r? {0,6})", r"\\n", x.group(2).lstrip())
            + x.group(3),
            invalid_json,
        )
        preload = "\n".join([httpx.get(url).text for url in preload_script_urls])
        return cls(
            definition_dict=yaml.safe_load(fixed_json),
            preload=preload,
        )

    def output_yaml_file(self, dist_path: str) -> None:
        definitions = self.to_winconfig_definition()

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

        Path(dist_path).write_text(yaml_str, encoding="utf-8")
        subprocess.run(["bunx", "prettier", "--write", f'"{dist_path}"'], check=True)

    def to_winconfig_definition(self) -> DefinitionContainer:
        return DefinitionContainer(
            definitions=[
                Definition(
                    id=re.sub(r"WPFToggle|WPFTweaks", "", _id),
                    name=capitalize(
                        re.sub(r"( [^\s\w]|[^\s\w] ).*", "", winutil_def.Content)
                    ),
                    description=winutil_def.Description,
                    registries=[
                        Registry(
                            path=registry.Path,
                            name=registry.Name,
                            type=registry.Type,
                            old_value=registry.OriginalValue.replace(
                                "<RemoveEntry>", NOT_EXIST
                            ),
                            new_value=registry.Value.replace(
                                "<RemoveEntry>", NOT_EXIST
                            ),
                        )
                        for registry in winutil_def.registry
                    ],
                    scheduled_tasks=[
                        ScheduledTask(
                            full_path=scheduled_task.Name,
                            old_state=scheduled_task.OriginalState,
                            new_state=scheduled_task.State,
                        )
                        for scheduled_task in winutil_def.ScheduledTask
                    ],
                    services=[
                        Service(
                            name=service.Name,
                            old_startup_type=service.OriginalType,
                            new_startup_type=service.StartupType,
                        )
                        for service in winutil_def.service
                    ],
                    script=Script(
                        apply="\n".join(winutil_def.InvokeScript or []).rstrip()
                        or None,
                        revert="\n".join(winutil_def.UndoScript or []).rstrip() or None,
                    ),
                )
                for _id, winutil_def in self.definition_dict.items()
                if winutil_def.Description != ""
            ],
            preload=self.preload,
        )
